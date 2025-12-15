from typing import Protocol

from sebastian.protocols.google_drive.models import UploadFileRequest, UploadFileResponse


class IGoogleDriveClient(Protocol):
    """Protocol for Google Drive client operations."""

    def upload_file(self, request: UploadFileRequest) -> UploadFileResponse:
        """Upload a file to Google Drive."""
        ...
