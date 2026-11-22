from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore

from sebastian.domain.gdrive import UploadFileRequest, UploadFileResponse

from .find_file import find_file_with_path  # type: ignore
from .upload_file import upload_file_with_path  # type: ignore


class GoogleDriveClient:
    """Client for interacting with Google Drive API."""

    def __init__(self, credentials: Credentials) -> None:
        """Initialize the Google Drive client with credentials.

        Args:
            credentials: Google OAuth2 credentials for authentication
        """
        self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)  # type: ignore

    def upload_file(self, request: UploadFileRequest) -> UploadFileResponse:
        """Upload a file to Google Drive.

        If the filename contains a path (e.g., "sub1/sub2/example.txt"), the necessary
        folder structure will be created automatically under the specified folder_id.

        Args:
            request: Upload request containing filename, content, folder_id, and mime_type

        Returns:
            UploadFileResponse containing the uploaded file's ID
        """
        file_id = upload_file_with_path(
            service=self._service,  # type: ignore
            filename_with_path=request.filename,
            content=request.content,
            base_folder_id=request.folder_id,
            mime_type=request.mime_type,
        )

        return UploadFileResponse(file_id=file_id)

    def find_file(self, filename_with_path: str, base_folder_id: str) -> str | None:
        """Find a file by its full path inside a base folder.

        Args:
            filename_with_path: Path like "sub1/sub2/example.txt", relative to base_folder_id
            base_folder_id: ID of the folder the search starts from

        Returns:
            The file's ID, or None when no file exists at that path
        """
        return find_file_with_path(
            service=self._service,  # type: ignore
            filename_with_path=filename_with_path,
            base_folder_id=base_folder_id,
        )
