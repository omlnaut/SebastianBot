from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sebastian.domain.delivery_ready_task_note import DeliveryReadyTaskNote
from sebastian.domain.gmail import FullMailResponse, GmailLabel
from sebastian.domain.side_effect import CreateTask, ModifyMailLabel, SendMessage
from sebastian.usecases.features.delivery_ready.handler import Handler
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
        subject="Paket zur Abholung bereit",
        snippet="From: pickup-point@amazon.de",
        sizeEstimate=123,
        historyId="hist-1",
        internalDate=str(internal_ms),
        content="<html><body>From: pickup-point@amazon.de demo</body></html>",
        pdf_parts=[],
    )


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


def _handler(gemini: _FakeGeminiClient) -> Handler:
    return Handler(
        gmail_client=None,
        gemini_client=gemini,
        retry_configuration=GeminiRetryConfiguration(immediate_retry_delay_seconds=0.0),
    )


def test_delivery_ready_check_if_mail_matches_from_saved_mail_fixture():
    fixture_path = (
        Path(__file__).parent / "fixtures" / "delivery_ready_matching_mail.json"
    )
    mail_payload = json.loads(fixture_path.read_text())
    mail = FullMailResponse.model_validate(mail_payload)

    handler = _handler(_FakeGeminiClient([]))

    assert handler.check_if_mail_matches(mail) is True


def test_delivery_ready_check_if_mail_matches_requires_subject_and_sender_marker():
    mail = _mail(datetime.now(timezone.utc))
    handler = _handler(_FakeGeminiClient([]))

    assert handler.check_if_mail_matches(mail) is True

    wrong_subject_mail = mail.model_copy(update={"subject": "Completely different"})
    assert handler.check_if_mail_matches(wrong_subject_mail) is False

    wrong_sender_mail = mail.model_copy(
        update={
            "snippet": "From: updates@example.com",
            "content": "<html><body>no sender marker</body></html>",
        }
    )
    assert handler.check_if_mail_matches(wrong_sender_mail) is False


def test_delivery_ready_transient_retry_then_success():
    mail = _mail(datetime.now(timezone.utc))
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

    result = _handler(gemini).handle_mail(mail)

    assert gemini.calls == 2
    create_task_effects = [e for e in result if isinstance(e, CreateTask)]
    assert len(create_task_effects) == 1
    label_effects = [e for e in result if isinstance(e, ModifyMailLabel)]
    assert len(label_effects) == 2
    assert any(effect.remove_labels for effect in label_effects)
    assert any(effect.add_labels for effect in label_effects)

    parsed_note = DeliveryReadyTaskNote.from_text(create_task_effects[0].notes)
    assert parsed_note.tracking_number == "T123"
    assert parsed_note.has_delivery_ready_tag is True


def test_delivery_ready_transient_retry_stays_unread():
    mail = _mail(datetime.now(timezone.utc))
    gemini = _FakeGeminiClient(
        [
            TransientGeminiError("model overloaded"),
            TransientGeminiError("still overloaded"),
        ]
    )

    result = _handler(gemini).handle_mail(mail)

    assert gemini.calls == 2
    assert result == []


def test_delivery_ready_non_retryable_marks_read_and_escalates():
    mail = _mail(datetime.now(timezone.utc))
    gemini = _FakeGeminiClient([NonRetryableGeminiError("schema mismatch")])

    result = _handler(gemini).handle_mail(mail)

    assert len([e for e in result if isinstance(e, SendMessage)]) == 1
    assert len([e for e in result if isinstance(e, ModifyMailLabel)]) == 1
    assert not any(
        GmailLabel.Processed in effect.add_labels
        for effect in result
        if isinstance(effect, ModifyMailLabel)
    )


def test_delivery_ready_old_mail_marks_read_and_escalates_without_gemini_call():
    old_mail = _mail(datetime.now(timezone.utc) - timedelta(days=8))
    gemini = _FakeGeminiClient([])

    result = _handler(gemini).handle_mail(old_mail)

    assert gemini.calls == 0
    assert len([e for e in result if isinstance(e, SendMessage)]) == 1
    assert len([e for e in result if isinstance(e, ModifyMailLabel)]) == 1
