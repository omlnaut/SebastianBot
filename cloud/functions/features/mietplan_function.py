import json
import logging
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta

import azure.functions as func
from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_mietplan
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.clients.mietplan.errors import MietplanAuthError
from sebastian.usecases.features import mietplan

from ..TriggerTimes import TriggerTimes

# The timer's window, and the resync default when ``maxFileAge`` is absent.
_DEFAULT_MAX_FILE_AGE = timedelta(days=1)
# Beyond this a window is "effectively all" and would overflow date arithmetic.
_MAX_FILE_AGE_DAYS = 365_000


class UsageError(Exception):
    """The query string does not describe a valid resync run."""


@dataclass(frozen=True)
class ResyncQuery:
    """One validated resync request, before it becomes a usecase ``Request``."""

    max_file_age: timedelta | None
    folder: str | None
    dry_run: bool

    def to_request(self) -> mietplan.Request:
        return mietplan.Request(
            max_file_age=self.max_file_age,
            folder=self.folder,
            dry_run=self.dry_run,
        )


@app.timer_trigger(
    schedule=TriggerTimes.Mietplan,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_mietplan(
    mytimer: TimerRequest,
) -> None:
    _run_timer_sync()


@app.route(route="check_mietplan")
def check_mietplan_http(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger: check_mietplan")
    return handle_resync(req.params)


def handle_resync(
    params: Mapping[str, str],
    resolve_handler: Callable[[], mietplan.Handler] = resolve_mietplan,
) -> func.HttpResponse:
    """Run one resync from query parameters and answer with its report.

    Takes a plain mapping instead of an ``HttpRequest`` and an injected handler,
    so parsing and serialisation are testable without Azure types. The side
    effects the handler returns are deliberately discarded: an HTTP-triggered
    run answers with the report and never sends a Telegram message.
    """
    started = time.monotonic()
    try:
        query = parse_resync_query(params)
    except UsageError as error:
        return _json_response(
            {"error": {"kind": "usage", "message": str(error)}}, status_code=400
        )

    try:
        handler = resolve_handler()
        handler.handle(query.to_request())
    except MietplanAuthError as error:
        logging.exception("Resync failed authentication")
        return _json_response(
            {"error": {"kind": "auth", "message": str(error)}}, status_code=500
        )
    except Exception as error:
        logging.exception("Resync failed")
        return _json_response(
            {"error": {"kind": "api", "message": str(error)}}, status_code=500
        )
    duration_seconds = time.monotonic() - started

    return _json_response(
        build_report_payload(query, handler.report, duration_seconds),
        status_code=200,
    )


def parse_resync_query(params: Mapping[str, str]) -> ResyncQuery:
    """Validate the resync query parameters; anything invalid raises ``UsageError``."""
    return ResyncQuery(
        max_file_age=_parse_max_file_age(params.get("maxFileAge")),
        folder=_parse_folder(params.get("folder")),
        dry_run=_parse_dry_run(params.get("dryRun")),
    )


def build_report_payload(
    query: ResyncQuery,
    report: mietplan.SyncReport,
    duration_seconds: float,
) -> dict[str, object]:
    """The resync response body: effective parameters plus per-file outcomes."""
    return {
        "dryRun": query.dry_run,
        "maxFileAge": "all" if query.max_file_age is None else query.max_file_age.days,
        "folder": query.folder,
        "scannedFolders": report.scanned_folders,
        "uploaded": list(report.uploaded),
        "replaced": list(report.replaced),
        "failed": [
            {"path": failure.path, "error": failure.error}
            for failure in report.failed
        ],
        "durationSeconds": round(duration_seconds, 1),
    }


def _parse_max_file_age(raw: str | None) -> timedelta | None:
    if raw is None:
        return _DEFAULT_MAX_FILE_AGE
    if raw == "all":
        return None
    if raw.isascii() and raw.isdigit():
        days = int(raw)
        if 0 < days <= _MAX_FILE_AGE_DAYS:
            return timedelta(days=days)
    raise UsageError(
        f'invalid maxFileAge: "{raw}" (expected "all" or a positive number of days)'
    )


def _parse_folder(raw: str | None) -> str | None:
    return raw or None


def _parse_dry_run(raw: str | None) -> bool:
    if raw is None:
        return False
    if raw in ("true", "1"):
        return True
    if raw in ("false", "0"):
        return False
    raise UsageError(f'invalid dryRun: "{raw}" (expected true, false, 1 or 0)')


def _json_response(
    payload: Mapping[str, object], status_code: int
) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
    )


def _run_timer_sync() -> None:
    logging.info("Checking for new mietplan files")

    perform_usecase_from_request(
        mietplan.Request(max_file_age=_DEFAULT_MAX_FILE_AGE), resolve_mietplan
    )
