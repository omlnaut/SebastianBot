from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sebastian.domain.gmail import FullMailResponse
from sebastian.domain.side_effect import CreateTask, ModifyMailLabel, SendMessage
from sebastian.usecases.features.return_tracker.handler import Handler, Request
from sebastian.usecases.shared.gemini_exceptions import (
    GeminiRetryConfiguration,
    NonRetryableGeminiError,
    TransientGeminiError,
)


def _mail(internal_date: datetime, content: str) -> FullMailResponse:
    internal_ms = int(internal_date.timestamp() * 1000)
    return FullMailResponse(
        id="mail-1",
        threadId="thread-1",
        labelIds=["UNREAD"],
        is_read=False,
        subject="Return request accepted",
        snippet="snippet",
        sizeEstimate=123,
        historyId="hist-1",
        internalDate=str(internal_ms),
        content=content,
        pdf_parts=[],
    )


class _FakeGmailClient:
    def __init__(self, mails: list[FullMailResponse]):
        self._mails = mails
        self.last_query: str | None = None

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        self.last_query = query
        return self._mails


class _FakeGeminiClient:
    def __init__(self, outcomes: list[Any]):
        self._outcomes = outcomes
        self.calls = 0

    def get_response(self, prompt: str, response_schema: type[Any]) -> Any:
        self.calls += 1
        outcome = self._outcomes[self.calls - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return response_schema.model_validate(outcome)


def test_return_tracker_transient_retry_then_success():
    content = "Deine Rückgabeanfrage wurde akzeptiert"
    gmail = _FakeGmailClient([_mail(datetime.now(timezone.utc), content=content)])
    gemini = _FakeGeminiClient(
        [
            TransientGeminiError("model overloaded"),
            {
                "return_date": "20.05.2026",
                "order_number": "D01",
                "pickup_location": "DHL Shop",
                "item_title": "Item",
            },
        ]
    )

    result = Handler(
        gmail_client=gmail,
        gemini_client=gemini,
        retry_configuration=GeminiRetryConfiguration(immediate_retry_delay_seconds=0.0),
    ).handle(Request())

    assert gmail.last_query is not None
    assert "is:unread" in gmail.last_query
    assert gemini.calls == 2
    assert len([e for e in result if isinstance(e, CreateTask)]) == 1
    assert len([e for e in result if isinstance(e, ModifyMailLabel)]) == 1


def test_return_tracker_non_retryable_marks_read_and_escalates():
    content = "Deine Rückgabeanfrage wurde akzeptiert"
    gmail = _FakeGmailClient([_mail(datetime.now(timezone.utc), content=content)])
    gemini = _FakeGeminiClient([NonRetryableGeminiError("schema mismatch")])

    result = Handler(
        gmail_client=gmail,
        gemini_client=gemini,
        retry_configuration=GeminiRetryConfiguration(),
    ).handle(Request())

    assert len([e for e in result if isinstance(e, SendMessage)]) == 1
    assert len([e for e in result if isinstance(e, ModifyMailLabel)]) == 1


def test_return_tracker_old_mail_marks_read_and_escalates_without_gemini_call():
    old_mail = _mail(
        datetime.now(timezone.utc) - timedelta(days=8),
        content="Deine Rückgabeanfrage wurde akzeptiert",
    )
    gmail = _FakeGmailClient([old_mail])
    gemini = _FakeGeminiClient([])

    result = Handler(
        gmail_client=gmail,
        gemini_client=gemini,
        retry_configuration=GeminiRetryConfiguration(),
    ).handle(Request())

    assert gemini.calls == 0
    assert len([e for e in result if isinstance(e, SendMessage)]) == 1
    assert len([e for e in result if isinstance(e, ModifyMailLabel)]) == 1
