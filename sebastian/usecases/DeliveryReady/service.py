from datetime import datetime, timedelta, timezone
import logging

from sebastian.protocols.google_task.models import TaskListIds
from sebastian.protocols.models import AllActor, CreateTask, SendMessage
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.protocols.gmail import IGmailClient
from sebastian.shared import Result

from .models import PickupData
from .parsing import parse_dhl_pickup_email_html


class DeliveryReadyService:
    def __init__(self, gmail_client: IGmailClient):
        self.gmail_client = gmail_client

    def get_recent_dhl_pickups(self, hours_back: int = 720) -> AllActor:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        query = (
            GmailQueryBuilder()
            .from_email("order-update@amazon.de")
            .subject("Ihr Paket kann bei DHL", exact=True)
            .after_date(time_threshold)
            .build()
        )

        try:
            # todo make client call safe, return Result type
            mails = self.gmail_client.fetch_mails(query)
            logging.info(f"Fetched {len(mails)} emails matching DHL pickup criteria")
        except Exception as e:
            return AllActor(
                create_tasks=[],
                send_messages=[SendMessage(message=f"Error fetching emails: {str(e)}")],
            )

        pickups: list[CreateTask] = []
        errors: list[SendMessage] = []

        for mail in mails:
            try:
                pickup_data = parse_dhl_pickup_email_html(mail.payload)
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

    return CreateTask(title=title, notes=notes, task_list_id=TaskListIds.Default)
