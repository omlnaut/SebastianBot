from typing import Protocol

from sebastian.clients.google.drive.models import UploadFileRequest, UploadFileResponse


class IGoogleDriveClient(Protocol):
    """Protocol for Google Drive client operations."""

    def upload_file(self, request: UploadFileRequest) -> UploadFileResponse:
        """Upload a file to Google Drive."""
        ...
