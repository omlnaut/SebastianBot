import logging
import time
from datetime import datetime, timezone
from typing import Sequence

from sebastian.domain.delivery_ready_task_note import DeliveryReadyTaskNote
from sebastian.domain.gmail import FullMailResponse
from sebastian.domain.side_effect import (
    CreateTask,
    ModifyMailLabel,
    SendMessage,
    SideEffect,
)
from sebastian.domain.task import TaskLists
from sebastian.usecases.shared.gemini_exceptions import (
    GeminiRetryConfiguration,
    TransientGeminiError,
)

from .parsing import PickupData, parse_dhl_pickup_email_html
from .protocols import GeminiClient

__all__ = [
    "Handler",
    "GeminiClient",
]


class Handler:
    def __init__(
        self,
        gemini_client: GeminiClient,
        retry_configuration: GeminiRetryConfiguration,
    ):
        self._gemini_client = gemini_client
        self._retry_configuration = retry_configuration

    def check_if_mail_matches(self, mail: FullMailResponse) -> bool:
        return _subject_matches(mail.subject) and _sender_matches(mail)

    def handle_mail(
        self,
        mail: FullMailResponse,
        now: datetime | None = None,
    ) -> Sequence[SideEffect]:
        if now is None:
            now = datetime.now(timezone.utc)

        age = mail.age(now)
        if age is None:
            return _terminal_failure_effects(
                mail,
                reason=f"Invalid internalDate: {mail.internalDate}",
            )

        if age > self._retry_configuration.retry_horizon:
            return _terminal_failure_effects(
                mail,
                reason=f"Retry horizon exceeded ({age})",
            )

        try:
            pickup_data = _parse_with_transient_retry(
                mail.content,
                self._gemini_client,
                self._retry_configuration.immediate_retry_delay_seconds,
            )
            return [
                _map_to_create_task(pickup_data),
                ModifyMailLabel.MarkAsRead(mail.id),
                ModifyMailLabel.MarkAsProcessed(mail.id),
            ]
        except TransientGeminiError as e:
            logging.warning(
                f"Transient Gemini error for delivery notification {mail.id}. Keeping unread for retry. Error: {str(e)}"
            )
            return []
        except Exception as e:
            return _terminal_failure_effects(
                mail,
                reason=f"Parsing failed: {str(e)}",
            )


def _subject_matches(subject: str) -> bool:
    return subject.strip().casefold() == "Paket zur Abholung bereit".casefold()


def _sender_matches(mail: FullMailResponse) -> bool:
    return mail.from_email.strip().casefold() == "pickup-point@amazon.de"


def _parse_with_transient_retry(
    html: str,
    gemini_client: GeminiClient,
    immediate_retry_delay_seconds: float,
) -> PickupData:
    try:
        return parse_dhl_pickup_email_html(html, gemini_client)
    except TransientGeminiError:
        time.sleep(immediate_retry_delay_seconds)
        return parse_dhl_pickup_email_html(html, gemini_client)


def _terminal_failure_effects(mail: FullMailResponse, reason: str) -> list[SideEffect]:
    return [
        SendMessage(
            message=(
                "Delivery Notification processing failed terminally. "
                f"subject={mail.subject}; reason={reason}"
            )
        ),
        ModifyMailLabel.MarkAsRead(mail.id),
    ]


def _map_to_create_task(pickup: PickupData) -> CreateTask:
    title = f"Paket abholen: {pickup.item}"
    notes = DeliveryReadyTaskNote.from_pickup_data(pickup).to_text()
    return CreateTask(title=title, notes=notes, tasklist=TaskLists.Default)
