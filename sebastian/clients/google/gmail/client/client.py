from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ..models import FullMailResponse
from .fetch_mails import fetch_full_mail, fetch_message_ids


class GmailClient:
    def __init__(self, credentials: Credentials):
        self._service = build(
            "gmail", "v1", credentials=credentials, cache_discovery=False
        )

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        """Fetch full email messages matching the query. Use the GmailQueryBuilder to build the query."""
        message_ids = fetch_message_ids(self._service, query)
        emails = [fetch_full_mail(self._service, msg_id.id) for msg_id in message_ids]
        return emails
