from io import BytesIO

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from sebastian.clients.google.drive.models import UploadFileRequest, UploadFileResponse


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

        Args:
            request: Upload request containing filename, content, folder_id, and mime_type

        Returns:
            UploadFileResponse containing the uploaded file's ID
        """
        bytes_content = BytesIO(request.content)

        file_metadata = {"name": request.filename, "parents": [request.folder_id]}

        media = MediaIoBaseUpload(
            bytes_content, mimetype=request.mime_type, resumable=True
        )

        uploaded_file = (
            self._service.files()  # type: ignore
            .create(
                body=file_metadata,
                media_body=media,
                fields="id",
            )
            .execute()
        )

        return UploadFileResponse(file_id=uploaded_file["id"])
