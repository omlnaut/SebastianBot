import logging
import os
from datetime import datetime, timezone

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_mail_check
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import mail_check

from ..TriggerTimes import TriggerTimes

_CUTOFF_DATE_ENV = "MAIL_CHECK_CUTOFF_DATE"


def _load_cutoff_date() -> datetime:
    raw = os.environ.get(_CUTOFF_DATE_ENV)
    if not raw:
        raise ValueError(
            f"Environment variable '{_CUTOFF_DATE_ENV}' is not set. "
            "Set it to an ISO 8601 datetime string (e.g. '2025-01-01T00:00:00+00:00'). "
            "Naive datetimes (without timezone offset) are interpreted as UTC."
        )
    try:
        cutoff = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable '{_CUTOFF_DATE_ENV}' contains an invalid datetime string: {raw!r}. "
            "Expected ISO 8601 format (e.g. '2025-01-01T00:00:00+00:00')."
        ) from exc
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    return cutoff


@app.timer_trigger(
    schedule=TriggerTimes.MailCheck,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_mail(mytimer: TimerRequest) -> None:
    logging.info("MailCheck timer function processed a request.")
    cutoff_date = _load_cutoff_date()
    perform_usecase_from_request(
        mail_check.Request(cutoff_date=cutoff_date),
        resolve_mail_check,
    )
