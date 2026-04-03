import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sebastian.domain.task import TaskLists
from sebastian.protocols.models import BaseActorEvent, CreateTask, SendMessage
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.usecases.usecase_handler import UseCaseHandler

from .parsing import PickupData, parse_dhl_pickup_email_html
from .protocols import GeminiClient, GmailClient

__all__ = ["Request", "Handler", "GmailClient", "GeminiClient"]


@dataclass
class Request:
    hours_back: timedelta = timedelta(hours=1)


class Handler(UseCaseHandler[Request]):
    def __init__(self, gmail_client: GmailClient, gemini_client: GeminiClient):
        self.gmail_client = gmail_client
        self.gemini_client = gemini_client

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        time_threshold = datetime.now(timezone.utc) - request.hours_back

        query = (
            GmailQueryBuilder()
            .from_email("order-update@amazon.de")
            .subject("Ihr Paket kann bei DHL", exact=True)
            .after_date(time_threshold)
            .build()
        )

        mails = self.gmail_client.fetch_mails(query)
        logging.info(f"Fetched {len(mails)} emails matching DHL pickup criteria")

        pickups: list[CreateTask] = []
        errors: list[SendMessage] = []

        for mail in mails:
            try:
                pickup_data = parse_dhl_pickup_email_html(
                    mail.content, self.gemini_client
                )
                pickups.append(_map_to_create_task(pickup_data))
            except Exception as e:
                errors.append(SendMessage(message=f"Error parsing email: {str(e)}"))

        return pickups + errors


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

    return CreateTask(title=title, notes=notes, tasklist=TaskLists.Default)
