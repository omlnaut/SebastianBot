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

    def add_tag(self, email_id: str, tag: GmailTag) -> None:
        """Add a tag/label to an email."""
        ...
