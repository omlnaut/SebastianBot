from typing import Protocol

from sebastian.domain.gmail import FullMailResponse, PdfAttachment


class GmailClient(Protocol):
    def fetch_mails(self, query: str) -> list[FullMailResponse]: ...

    def download_pdf_attachments(
        self, mail: FullMailResponse
    ) -> list[PdfAttachment]: ...
