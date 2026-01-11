from typing import Protocol

from .models import FullMailResponse, PdfAttachment


class IGmailClient(Protocol):
    """Protocol for Gmail client operations."""

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        """Fetch full email messages matching the query."""
        ...

    def download_pdf_attachments(self, mail: FullMailResponse) -> list[PdfAttachment]:
        """Download PDF attachments from a full email message."""
        ...
