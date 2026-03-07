# pyright: basic

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.clients.google.gmail.client.retry_decorator import retry_on_network_error
from sebastian.protocols.gmail.models import FullMailResponse, MessageId


class GmailServiceWrapper:
    def __init__(self, credentials: Credentials):
        self._credentials = credentials
        self._service = build(
            "gmail", "v1", credentials=credentials, cache_discovery=False
        )

    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_message_ids(self, query: str) -> list[MessageId]:
        """Fetch message IDs matching the query."""
        response = self._service.users().messages().list(userId="me", q=query).execute()
        messages = response.get("messages", [])
        ids = [msg["id"] for msg in messages]

        return [MessageId(id=id) for id in ids]

    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_full_mail(self, msg_id: str) -> FullMailResponse:
        """Fetch full email message by ID"""
        message = (
            self._service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
        return FullMailResponse.from_response(message)
