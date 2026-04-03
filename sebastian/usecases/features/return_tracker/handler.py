import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sebastian.domain.task import TaskLists
from sebastian.protocols.models import BaseActorEvent, CreateTask, SendMessage
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.usecases.usecase_handler import UseCaseHandler

from .parsing import ReturnData, parse_return_email_html
from .protocols import GeminiClient, GmailClient

__all__ = ["Request", "Handler", "GmailClient", "GeminiClient"]


@dataclass
class Request:
    time_back: timedelta = timedelta(hours=1)


class Handler(UseCaseHandler[Request]):
    def __init__(self, gmail_client: GmailClient, gemini_client: GeminiClient):
        self._gmail_client = gmail_client
        self._gemini_client = gemini_client

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        time_threshold = datetime.now(timezone.utc) - request.time_back

        query = (
            GmailQueryBuilder()
            .from_email("rueckgabe@amazon.de")
            .subject("Ihre Rücksendung von", exact=False)
            .after_date(time_threshold)
            .build()
        )

        mails = self._gmail_client.fetch_mails(query)
        logging.info(f"Fetched {len(mails)} return emails from Amazon")

        tasks: list[CreateTask] = []
        errors: list[SendMessage] = []

        for mail in mails:
            try:
                return_data = parse_return_email_html(mail.content, self._gemini_client)
                tasks.append(_map_to_create_task(return_data))
            except Exception as e:
                errors.append(SendMessage(message=f"Error parsing email: {str(e)}"))

        return tasks + errors


def _map_to_create_task(return_data: ReturnData) -> CreateTask:
    title = "Retoure"
    notes = (
        f"{return_data.item_title}\n"
        f"Abholort: {return_data.pickup_location}\n"
        f"Retoure bis: {return_data.return_date}\n"
        f"Order: {return_data.order_number}"
    )
    return CreateTask(title=title, notes=notes, tasklist=TaskLists.Default)
