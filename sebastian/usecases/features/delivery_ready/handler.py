from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging


from sebastian.domain.task import TaskLists
from sebastian.protocols.models import AllActor, CreateTask, SendMessage
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.usecases.usecase_handler import UseCaseHandler

from .parsing import PickupData, parse_dhl_pickup_email_html
from .protocols import GmailClient

__all__ = ["Request", "Handler", "GmailClient"]


@dataclass
class Request:
    hours_back: int = 720


class Handler(UseCaseHandler[Request]):
    def __init__(self, gmail_client: GmailClient):
        self.gmail_client = gmail_client

    def handle(self, request: Request) -> AllActor:
        time_threshold = datetime.now(timezone.utc) - timedelta(
            hours=request.hours_back
        )

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
                pickup_data = parse_dhl_pickup_email_html(mail.content)
                pickups.append(_map_to_create_task(pickup_data))
            except Exception as e:
                errors.append(SendMessage(message=f"Error parsing email: {str(e)}"))

        return AllActor(create_tasks=pickups, send_messages=errors)


def _map_to_create_task(pickup: PickupData) -> CreateTask:
    title = f"Paket abholen: {pickup.preview}"

    notes = ""
    if pickup.preview:
        notes += f"{pickup.preview}"
    notes += f"\nAbholort: {pickup.pickup_location}"
    if pickup.due_date:
        notes += f"\nBis: {pickup.due_date}"
    if pickup.tracking_number:
        notes += f"\nTracking: {pickup.tracking_number}"

    return CreateTask(title=title, notes=notes, tasklist=TaskLists.Default)
