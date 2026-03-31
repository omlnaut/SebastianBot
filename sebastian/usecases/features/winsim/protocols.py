from typing import Protocol

from sebastian.domain.gmail import FullMailResponse, PdfAttachment
from sebastian.protocols.google_drive import UploadFileRequest, UploadFileResponse

__all__ = ["GmailClient", "GoogleDriveClient"]


class GmailClient(Protocol):
    def fetch_mails(self, query: str) -> list[FullMailResponse]: ...

    def download_pdf_attachments(
        self, mail: FullMailResponse
    ) -> list[PdfAttachment]: ...


class GoogleDriveClient(Protocol):
    def upload_file(self, request: UploadFileRequest) -> UploadFileResponse: ...
