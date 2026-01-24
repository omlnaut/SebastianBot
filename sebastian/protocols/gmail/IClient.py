from typing import Protocol

from .models import FullMailResponse, GmailTag, PdfAttachment


class IGmailClient(Protocol):
    """Protocol for Gmail client operations."""

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        """Fetch full email messages matching the query."""
        ...

    def download_pdf_attachments(self, mail: FullMailResponse) -> list[PdfAttachment]:
        """Download PDF attachments from a full email message."""
        ...

    def modify_labels(
        self,
        email_id: str,
        add_labels: list[GmailTag] | None = None,
        remove_labels: list[GmailTag] | None = None,
    ) -> None:
        """Modify labels on an email by adding and/or removing tags."""
        ...
