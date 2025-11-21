import os
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

    def _find_or_create_folder(self, folder_name: str, parent_id: str) -> str:
        """Find a folder by name within a parent folder, or create it if it doesn't exist.

        Args:
            folder_name: Name of the folder to find or create
            parent_id: ID of the parent folder

        Returns:
            The ID of the found or created folder
        """
        # Search for existing folder
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = (
            self._service.files().list(q=query, fields="files(id, name)").execute()  # type: ignore
        )
        items = results.get("files", [])

        if items:
            # Folder exists, return its ID
            return items[0]["id"]

        # Folder doesn't exist, create it
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = self._service.files().create(body=file_metadata, fields="id").execute()  # type: ignore
        return folder["id"]

    def _ensure_folder_path(self, path: str, base_folder_id: str) -> str:
        """Navigate or create a folder path, returning the ID of the final folder.

        Args:
            path: Folder path like "sub1/sub2/sub3"
            base_folder_id: ID of the base folder to start from

        Returns:
            The ID of the final folder in the path
        """
        current_parent_id = base_folder_id

        # Split path and create each folder in sequence
        for folder_name in path.split("/"):
            if folder_name:  # Skip empty strings
                current_parent_id = self._find_or_create_folder(
                    folder_name, current_parent_id
                )

        return current_parent_id

    def upload_file(self, request: UploadFileRequest) -> UploadFileResponse:
        """Upload a file to Google Drive.

        If the filename contains a path (e.g., "sub1/sub2/example.txt"), the necessary
        folder structure will be created automatically under the specified folder_id.

        Args:
            request: Upload request containing filename, content, folder_id, and mime_type

        Returns:
            UploadFileResponse containing the uploaded file's ID
        """
        # Split the path into directory and filename
        dir_path = os.path.dirname(request.filename)
        filename = os.path.basename(request.filename)

        # Navigate/create the folder structure if path is provided
        if dir_path:
            parent_folder_id = self._ensure_folder_path(dir_path, request.folder_id)
        else:
            parent_folder_id = request.folder_id

        # Upload the file to the final folder
        bytes_content = BytesIO(request.content)
        file_metadata = {"name": filename, "parents": [parent_folder_id]}

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
