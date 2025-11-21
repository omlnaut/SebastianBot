from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.clients.google.drive.models import UploadFileRequest, UploadFileResponse
from sebastian.clients.google.drive.upload_file import upload_file_with_path


class GoogleDriveClient:
    """Client for interacting with Google Drive API."""

    def __init__(self, credentials: Credentials) -> None:
        """Initialize the Google Drive client with credentials.

        Args:
            credentials: Google OAuth2 credentials for authentication
        """
        self._credentials = credentials
        self._service = build(
            "drive", "v3", credentials=credentials, cache_discovery=False
        )

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
            service=self._service,
            filename_with_path=request.filename,
            content=request.content,
            base_folder_id=request.folder_id,
            mime_type=request.mime_type,
        )

        return UploadFileResponse(file_id=file_id)
