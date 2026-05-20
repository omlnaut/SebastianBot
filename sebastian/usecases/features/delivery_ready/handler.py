import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sebastian.domain.gmail import FullMailResponse
from sebastian.domain.task import TaskTags, TaskLists
from sebastian.domain.side_effect import (
    SideEffect,
    CreateTask,
    ModifyMailLabel,
    SendMessage,
)
from sebastian.usecases.shared.query_builder import GmailQueryBuilder
from sebastian.usecases.shared.gemini_exceptions import (
    GeminiRetryConfiguration,
    TransientGeminiError,
)
from sebastian.usecases.usecase_handler import UseCaseHandler

from .parsing import PickupData, parse_dhl_pickup_email_html
from .protocols import GeminiClient, GmailClient

__all__ = [
    "Request",
    "Handler",
    "GmailClient",
    "GeminiClient",
]


@dataclass
class Request:
    pass


class Handler(UseCaseHandler[Request]):
    def __init__(
        self,
        gmail_client: GmailClient,
        gemini_client: GeminiClient,
        retry_configuration: GeminiRetryConfiguration,
    ):
        self.gmail_client = gmail_client
        self.gemini_client = gemini_client
        self.retry_configuration = retry_configuration

    def handle(self, request: Request) -> Sequence[SideEffect]:
        now = datetime.now(timezone.utc)
        mails = _fetch_pickup_mails(self.gmail_client)
        logging.info(f"Fetched {len(mails)} emails matching DHL pickup criteria")

        effects: list[SideEffect] = []

        for mail in mails:
            age = _mail_age(mail, now)
            if age is None:
                effects.extend(
                    _terminal_failure_effects(
                        mail,
                        reason=f"Invalid internalDate: {mail.internalDate}",
                    )
                )
                continue

            if age > self.retry_configuration.retry_horizon:
                effects.extend(
                    _terminal_failure_effects(
                        mail,
                        reason=f"Retry horizon exceeded ({age})",
                    )
                )
                continue

            try:
                pickup_data = _parse_with_transient_retry(
                    mail.content,
                    self.gemini_client,
                    self.retry_configuration.immediate_retry_delay_seconds,
                )
                effects.append(_map_to_create_task(pickup_data))
                effects.append(ModifyMailLabel.MarkAsRead(mail.id))
            except TransientGeminiError as e:
                logging.warning(
                    f"Transient Gemini error for delivery notification {mail.id}. Keeping unread for retry. Error: {str(e)}"
                )
            except Exception as e:
                effects.extend(
                    _terminal_failure_effects(mail, reason=f"Parsing failed: {str(e)}")
                )

        return effects


def _fetch_pickup_mails(gmail_client: GmailClient) -> Sequence[FullMailResponse]:
    query = (
        GmailQueryBuilder()
        .from_email("pickup-point.amazon.de")
        .subject("Paket zur Abholung bereit", exact=True)
        .is_unread()
        .build()
    )
    return gmail_client.fetch_mails(query)


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


def _mail_age(mail: FullMailResponse, now: datetime) -> timedelta | None:
    try:
        timestamp = int(mail.internalDate) / 1000
    except ValueError:
        return None

    received_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return now - received_at


def _terminal_failure_effects(
    mail: FullMailResponse, reason: str
) -> list[SideEffect]:
    return [
        SendMessage(
            message=(
                "Delivery Notification processing failed terminally. "
                f"mail_id={mail.id}; reason={reason}"
            )
        ),
        ModifyMailLabel.MarkAsRead(mail.id),
    ]


def _map_to_create_task(pickup: PickupData) -> CreateTask:
    title = f"Paket abholen: {pickup.item}"

    notes = ""
    if pickup.item:
        notes += f"{pickup.item}"
    notes += f"\nAbholort: {pickup.pickup_location}"
    if pickup.due_date:
        notes += f"\nBis: {pickup.due_date.strftime('%d.%m.%Y')}"
    if pickup.tracking_number:
        notes += f"\nTracking: {pickup.tracking_number}"
    notes += f"\n{TaskTags.DeliveryReady.value}"

    return CreateTask(title=title, notes=notes, tasklist=TaskLists.Default)
