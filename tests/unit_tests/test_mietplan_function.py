import json
from datetime import timedelta
from typing import Sequence

import pytest

# The Functions entry point imports the feature modules; importing it first mirrors
# the runtime and keeps that import graph from being circular from the test side.
import function_app
from cloud.functions.features import mietplan_function
from cloud.functions.features.mietplan_function import (
    UsageError,
    build_report_payload,
    handle_resync,
    parse_resync_query,
)
from cloud.functions.side_effects.send_message.models import (
    SendTelegramMessageEventGrid,
)
from sebastian.clients.mietplan.errors import MietplanAuthError
from sebastian.domain.side_effect import SendMessage, SideEffect
from sebastian.usecases.features import mietplan
from sebastian.usecases.features.mietplan.handler import (
    Request,
    SyncFailure,
    SyncReport,
)


class _FakeHandler:
    """The report is the only thing the route reads back from the handler."""

    def __init__(
        self,
        report: SyncReport | None = None,
        side_effects: Sequence[SideEffect] = (),
        error: Exception | None = None,
    ) -> None:
        self.report = report or SyncReport()
        self.side_effects = list(side_effects)
        self.error = error
        self.requests: list[Request] = []

    def handle(self, request: Request) -> Sequence[SideEffect]:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.side_effects


class _FakeResolver:
    def __init__(self, handler: _FakeHandler) -> None:
        self.handler = handler
        self.calls = 0

    def __call__(self) -> _FakeHandler:
        self.calls += 1
        return self.handler


def _payload_dict(response) -> dict[str, object]:
    return json.loads(response.get_body().decode())


def _no_side_effects_sent(monkeypatch) -> list[object]:
    sent: list[object] = []
    monkeypatch.setattr(
        "cloud.functions.side_effects.shared.send_eventgrid_events", sent.extend
    )
    return sent


def test_defaults_keep_the_timer_window_of_one_day():
    query = parse_resync_query({})

    assert query.max_file_age == timedelta(days=1)
    assert query.folder is None
    assert query.dry_run is False


def test_max_file_age_accepts_all_and_positive_day_counts():
    assert parse_resync_query({"maxFileAge": "all"}).max_file_age is None
    assert parse_resync_query({"maxFileAge": "1"}).max_file_age == timedelta(days=1)
    assert parse_resync_query({"maxFileAge": "30"}).max_file_age == timedelta(days=30)


@pytest.mark.parametrize(
    "raw", ["0", "-3", "abc", "1.5", "", "allx", "+3", "9999999999"]
)
def test_invalid_max_file_age_is_a_usage_error(raw: str):
    with pytest.raises(UsageError) as raised:
        parse_resync_query({"maxFileAge": raw})

    assert "maxFileAge" in str(raised.value)


@pytest.mark.parametrize(
    ("raw", "expected"), [("true", True), ("1", True), ("false", False), ("0", False)]
)
def test_dry_run_accepts_the_documented_tokens(raw: str, expected: bool):
    assert parse_resync_query({"dryRun": raw}).dry_run is expected


@pytest.mark.parametrize("raw", ["maybe", "", "TRUE", "yes"])
def test_invalid_dry_run_is_a_usage_error(raw: str):
    with pytest.raises(UsageError) as raised:
        parse_resync_query({"dryRun": raw})

    assert "dryRun" in str(raised.value)


def test_folder_scope_is_echoed_and_an_empty_scope_means_every_folder():
    assert parse_resync_query({"folder": "Archiv/2019"}).folder == "Archiv/2019"
    assert parse_resync_query({"folder": ""}).folder is None
    assert parse_resync_query({}).folder is None


def test_query_maps_onto_the_usecase_request():
    query = parse_resync_query({"maxFileAge": "all", "folder": "Archiv", "dryRun": "1"})

    assert query.to_request() == Request(
        max_file_age=None, folder="Archiv", dry_run=True
    )


def test_report_payload_has_exactly_the_documented_shape():
    report = SyncReport(
        uploaded=["Nebenkostenabrechnung/2024.pdf"],
        replaced=["Mietvertrag/mietvertrag.pdf"],
        failed=[SyncFailure(path="Archiv/2019/x.pdf", error="read timeout")],
        scanned_folders=42,
    )
    query = parse_resync_query({"maxFileAge": "all"})

    payload = build_report_payload(query, report, duration_seconds=63.44)

    assert payload == {
        "dryRun": False,
        "maxFileAge": "all",
        "folder": None,
        "scannedFolders": 42,
        "uploaded": ["Nebenkostenabrechnung/2024.pdf"],
        "replaced": ["Mietvertrag/mietvertrag.pdf"],
        "failed": [{"path": "Archiv/2019/x.pdf", "error": "read timeout"}],
        "durationSeconds": 63.4,
    }
    assert list(payload) == [
        "dryRun",
        "maxFileAge",
        "folder",
        "scannedFolders",
        "uploaded",
        "replaced",
        "failed",
        "durationSeconds",
    ]


def test_report_payload_echoes_a_day_count_and_the_folder_prefix():
    report = SyncReport()
    query = parse_resync_query({"maxFileAge": "7", "folder": "Archiv", "dryRun": "true"})

    payload = build_report_payload(query, report, duration_seconds=0.04)

    assert payload["dryRun"] is True
    assert payload["maxFileAge"] == "7"
    assert payload["folder"] == "Archiv"
    assert payload["durationSeconds"] == 0.0


def test_a_resync_run_returns_the_report_and_sends_no_side_effect(monkeypatch):
    sent = _no_side_effects_sent(monkeypatch)
    report = SyncReport(
        uploaded=["Miete/a.pdf"],
        replaced=["Miete/b.pdf"],
        failed=[SyncFailure(path="Miete/c.pdf", error="boom")],
        scanned_folders=3,
    )
    handler = _FakeHandler(report, side_effects=[SendMessage(message="should not send")])
    resolver = _FakeResolver(handler)

    response = handle_resync({"maxFileAge": "30", "folder": "Miete"}, resolver)

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert handler.requests == [
        Request(max_file_age=timedelta(days=30), folder="Miete", dry_run=False)
    ]
    payload = _payload_dict(response)
    assert payload["dryRun"] is False
    assert payload["maxFileAge"] == "30"
    assert payload["folder"] == "Miete"
    assert payload["scannedFolders"] == 3
    assert payload["uploaded"] == ["Miete/a.pdf"]
    assert payload["replaced"] == ["Miete/b.pdf"]
    assert payload["failed"] == [{"path": "Miete/c.pdf", "error": "boom"}]
    assert isinstance(payload["durationSeconds"], float)
    assert payload["durationSeconds"] >= 0.0
    assert sent == []


def test_a_dry_run_reaches_the_handler_and_is_echoed(monkeypatch):
    sent = _no_side_effects_sent(monkeypatch)
    handler = _FakeHandler(SyncReport(uploaded=["Miete/a.pdf"], scanned_folders=1))
    resolver = _FakeResolver(handler)

    response = handle_resync({"dryRun": "true"}, resolver)

    assert response.status_code == 200
    assert handler.requests == [
        Request(max_file_age=timedelta(days=1), folder=None, dry_run=True)
    ]
    payload = _payload_dict(response)
    assert payload["dryRun"] is True
    assert payload["maxFileAge"] == "1"
    assert payload["uploaded"] == ["Miete/a.pdf"]
    assert sent == []


@pytest.mark.parametrize(
    "params",
    [
        {"maxFileAge": "0"},
        {"maxFileAge": "-3"},
        {"maxFileAge": "soon"},
        {"dryRun": "maybe"},
    ],
)
def test_invalid_parameters_are_a_json_usage_error(monkeypatch, params):
    sent = _no_side_effects_sent(monkeypatch)
    resolver = _FakeResolver(_FakeHandler())

    response = handle_resync(params, resolver)

    assert response.status_code == 400
    assert response.mimetype == "application/json"
    payload = _payload_dict(response)
    assert list(payload) == ["error"]
    assert payload["error"]["kind"] == "usage"
    assert payload["error"]["message"]
    assert resolver.calls == 0
    assert sent == []


def test_a_handler_error_is_a_json_api_error_instead_of_a_bare_500(monkeypatch):
    sent = _no_side_effects_sent(monkeypatch)
    handler = _FakeHandler(error=RuntimeError("portal read timeout"))
    resolver = _FakeResolver(handler)

    response = handle_resync({}, resolver)

    assert response.status_code == 500
    assert response.mimetype == "application/json"
    assert _payload_dict(response) == {
        "error": {"kind": "api", "message": "portal read timeout"}
    }
    assert handler.requests == [
        Request(max_file_age=timedelta(days=1), folder=None, dry_run=False)
    ]
    assert sent == []


def test_an_auth_error_is_a_json_auth_error_instead_of_a_bare_500(monkeypatch):
    sent = _no_side_effects_sent(monkeypatch)
    handler = _FakeHandler(
        error=MietplanAuthError("login was rejected: HTTP 403", 403)
    )
    resolver = _FakeResolver(handler)

    response = handle_resync({}, resolver)

    assert response.status_code == 500
    assert response.mimetype == "application/json"
    assert _payload_dict(response) == {
        "error": {
            "kind": "auth",
            "message": "login was rejected: HTTP 403",
        }
    }
    assert sent == []


def test_a_resolver_error_is_a_json_api_error(monkeypatch):
    sent = _no_side_effects_sent(monkeypatch)

    def failing_resolver() -> _FakeHandler:
        raise ValueError("no credentials")

    response = handle_resync({}, failing_resolver)

    assert response.status_code == 500
    assert response.mimetype == "application/json"
    assert _payload_dict(response) == {
        "error": {"kind": "api", "message": "no credentials"}
    }
    assert sent == []


def test_the_timer_still_sends_its_telegram_summary(monkeypatch):
    sent = _no_side_effects_sent(monkeypatch)
    message = "Found new mietplan files:\n- Miete/a.pdf"
    handler = _FakeHandler(SyncReport(uploaded=["Miete/a.pdf"]), [SendMessage(message=message)])
    resolver = _FakeResolver(handler)
    monkeypatch.setattr(mietplan_function, "resolve_mietplan", resolver)

    mietplan_function.check_mietplan(None)  # type: ignore[arg-type]

    # The timer keeps its one-day window and its message; the side effect is sent.
    assert handler.requests == [
        mietplan.Request(max_file_age=timedelta(days=1), folder=None, dry_run=False)
    ]
    assert sent == [SendTelegramMessageEventGrid.from_application(SendMessage(message=message))]
