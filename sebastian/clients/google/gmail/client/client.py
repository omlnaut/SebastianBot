from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.protocols.gmail.models import FullMailResponse, PdfAttachment

from .download_pdf_attachments import download_pdf_attachments_from_messages
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

    def download_pdf_attachments(self, query: str) -> list[PdfAttachment]:
        """Download PDF attachments from messages matching the query. Use the GmailQueryBuilder to build the query."""
        messages = self.fetch_mails(query)
        return download_pdf_attachments_from_messages(self._service, messages)
