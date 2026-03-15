from datetime import datetime, timedelta, timezone

from sebastian.domain.task import TaskLists
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.protocols.gemini import IGeminiClient
from sebastian.protocols.models import AllActor, CreateTask, SendMessage

from .models import ReturnData
from .parsing import parse_return_email_html
from .protocols import GmailClient


class ReturnTrackerService:
    def __init__(self, gmail_client: GmailClient, gemini_client: IGeminiClient):
        self.gmail_client = gmail_client
        self.gemini_client = gemini_client

    def get_recent_returns(self, time_back: timedelta = timedelta(hours=1)) -> AllActor:
        """Fetch recent return emails within the given time delta.

        time_back: timedelta indicating how far back to search (e.g. timedelta(hours=1)).
        """
        time_threshold = datetime.now(timezone.utc) - time_back

        query = (
            GmailQueryBuilder()
            .from_email("rueckgabe@amazon.de")
            .subject("Ihre Rücksendung von", exact=False)
            .after_date(time_threshold)
            .build()
        )

        try:
            mails = self.gmail_client.fetch_mails(query)
        except Exception as e:
            return AllActor(
                create_tasks=[],
                send_messages=[SendMessage(message=f"Error fetching emails: {str(e)}")],
            )

        tasks: list[CreateTask] = []
        errors: list[SendMessage] = []

        for mail in mails:
            try:
                return_data = parse_return_email_html(mail.content, self.gemini_client)
                tasks.append(_map_to_create_task(return_data))
            except Exception as e:
                errors.append(SendMessage(message=f"Error parsing email: {str(e)}"))

        return AllActor(create_tasks=tasks, send_messages=errors)


def _map_to_create_task(return_data: ReturnData) -> CreateTask:
    title = "Retoure"
    notes = (
        f"{return_data.item_title}\n"
        f"Abholort: {return_data.pickup_location}\n"
        f"Retoure bis: {return_data.return_date}\n"
        f"Order: {return_data.order_number}"
    )
    return CreateTask(title=title, notes=notes, tasklist=TaskLists.Default)
