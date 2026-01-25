from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.clients.google.gmail.client.modify_labels import _modify_labels
from sebastian.protocols.gmail import FullMailResponse, GmailLabel, PdfAttachment

from .download_pdf_attachments import download_pdf_attachments_from_messages
from .fetch_mails import fetch_full_mail, fetch_message_ids


class GmailClient:
    def __init__(self, credentials: Credentials):
        self._service = build(
            "gmail", "v1", credentials=credentials, cache_discovery=False
        )

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        """Fetch full email messages matching the query. Use the GmailQueryBuilder from sebastian.shared.gmail to build the query."""
        message_ids = fetch_message_ids(self._service, query)
        emails = [fetch_full_mail(self._service, msg_id.id) for msg_id in message_ids]
        return emails

    def download_pdf_attachments(self, mail: FullMailResponse) -> list[PdfAttachment]:
        """Download PDF attachments from a full email message."""
        return download_pdf_attachments_from_messages(self._service, mail)

    def modify_labels(
        self,
        email_id: str,
        add_labels: list[GmailLabel] | None = None,
        remove_labels: list[GmailLabel] | None = None,
    ) -> None:
        """Modify labels on an email by adding and/or removing tags."""
        return _modify_labels(
            self._service,
            email_id=email_id,
            add_labels=add_labels,
            remove_labels=remove_labels,
        )
