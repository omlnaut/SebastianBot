from typing import Generator, Protocol

from sebastian.domain.gdrive import UploadFileRequest, UploadFileResponse
from sebastian.domain.mietplan import MietplanFolder


class IMietplanClient(Protocol):
    """Protocol for Mietplan client operations."""

    def walk_from_top_folder(self) -> Generator[MietplanFolder, None, None]:
        """Walk through all folders starting from the top folder."""
        ...

    def download_file(self, download_path: str) -> bytes:
        """Download a file from the given path."""
        ...


class IGoogleDriveClient(Protocol):
    """Protocol for Google Drive client operations."""

    def upload_file(self, request: UploadFileRequest) -> UploadFileResponse:
        """Upload a file to Google Drive, creating the folder path as needed."""
        ...

    def find_file(self, filename_with_path: str, base_folder_id: str) -> str | None:
        """Return the id of the file at that path inside the base folder, if any."""
        ...

    def replace_file(self, file_id: str, content: bytes, mime_type: str) -> None:
        """Replace the content of an existing file in place, keeping id and parents."""
        ...
