from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sebastian.domain.delivery_ready_task_note import DeliveryReadyTaskNote
from sebastian.domain.gmail import FullMailResponse
from sebastian.domain.side_effect import CreateTask, ModifyMailLabel, SendMessage
from sebastian.usecases.features.delivery_ready.handler import Handler, Request
from sebastian.usecases.shared.gemini_exceptions import (
    GeminiRetryConfiguration,
    NonRetryableGeminiError,
    TransientGeminiError,
)


def _mail(internal_date: datetime) -> FullMailResponse:
    internal_ms = int(internal_date.timestamp() * 1000)
    return FullMailResponse(
        id="mail-1",
        threadId="thread-1",
        labelIds=["UNREAD"],
        is_read=False,
        subject="Delivery update",
        snippet="snippet",
        sizeEstimate=123,
        historyId="hist-1",
        internalDate=str(internal_ms),
        content="<html><body>demo</body></html>",
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


def test_delivery_ready_transient_retry_then_success():
    gmail = _FakeGmailClient([_mail(datetime.now(timezone.utc))])
    gemini = _FakeGeminiClient(
        [
            TransientGeminiError("model overloaded"),
            {
                "tracking_number": "T123",
                "pickup_location": "Packstation 123",
                "due_date": "2026-05-20",
                "item": "Book",
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
    create_task_effects = [e for e in result if isinstance(e, CreateTask)]
    assert len(create_task_effects) == 1
    assert len([e for e in result if isinstance(e, ModifyMailLabel)]) == 1

    parsed_note = DeliveryReadyTaskNote.from_text(create_task_effects[0].notes)
    assert parsed_note.tracking_number == "T123"
    assert parsed_note.has_delivery_ready_tag is True


def test_delivery_ready_transient_retry_stays_unread():
    gmail = _FakeGmailClient([_mail(datetime.now(timezone.utc))])
    gemini = _FakeGeminiClient(
        [
            TransientGeminiError("model overloaded"),
            TransientGeminiError("still overloaded"),
        ]
    )

    result = Handler(
        gmail_client=gmail,
        gemini_client=gemini,
        retry_configuration=GeminiRetryConfiguration(immediate_retry_delay_seconds=0.0),
    ).handle(Request())

    assert gemini.calls == 2
    assert result == []


def test_delivery_ready_non_retryable_marks_read_and_escalates():
    gmail = _FakeGmailClient([_mail(datetime.now(timezone.utc))])
    gemini = _FakeGeminiClient([NonRetryableGeminiError("schema mismatch")])

    result = Handler(
        gmail_client=gmail,
        gemini_client=gemini,
        retry_configuration=GeminiRetryConfiguration(),
    ).handle(Request())

    assert len([e for e in result if isinstance(e, SendMessage)]) == 1
    assert len([e for e in result if isinstance(e, ModifyMailLabel)]) == 1


def test_delivery_ready_old_mail_marks_read_and_escalates_without_gemini_call():
    old_mail = _mail(datetime.now(timezone.utc) - timedelta(days=8))
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
