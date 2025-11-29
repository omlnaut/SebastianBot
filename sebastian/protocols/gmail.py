from typing import Protocol

from sebastian.clients.google.gmail.models import FullMailResponse, PdfAttachment


class GmailClientProtocol(Protocol):
    """Protocol for Gmail client operations."""

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        """Fetch full email messages matching the query."""
        ...

    def download_pdf_attachments(self, query: str) -> list[PdfAttachment]:
        """Download PDF attachments from messages matching the query."""
        ...
