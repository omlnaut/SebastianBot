from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .models import FullMailResponse, MessageId


class GmailClient:
    def __init__(self, credentials: Credentials):
        self._service = build(
            "gmail", "v1", credentials=credentials, cache_discovery=False
        )

    def _fetch_message_ids(self, query: str) -> list[MessageId]:
        """Fetch message IDs matching the query"""
        response = self._service.users().messages().list(userId="me", q=query).execute()
        messages = response.get("messages", [])
        return [MessageId.from_response(msg) for msg in messages]

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        """Fetch full email messages matching the query. Use the GmailQueryBuilder to build the query."""
        message_ids = self._fetch_message_ids(query)
        emails = []
        for msg_id in message_ids:
            message = (
                self._service.users()
                .messages()
                .get(userId="me", id=msg_id.id, format="full")
                .execute()
            )
            emails.append(FullMailResponse.from_response(message))
        return emails
