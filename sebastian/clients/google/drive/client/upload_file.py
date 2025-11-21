"""Helper functions for uploading files to Google Drive."""

import os
from io import BytesIO

from googleapiclient.http import MediaIoBaseUpload


def find_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    """Find a folder by name within a parent folder, or create it if it doesn't exist.

    Args:
        service: Google Drive API service instance
        folder_name: Name of the folder to find or create
        parent_id: ID of the parent folder

    Returns:
        The ID of the found or created folder
    """
    # Search for existing folder
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = (
        service.files().list(q=query, fields="files(id, name)").execute()  # type: ignore
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
    folder = service.files().create(body=file_metadata, fields="id").execute()  # type: ignore
    return folder["id"]


def ensure_folder_path(service, path: str, base_folder_id: str) -> str:
    """Navigate or create a folder path, returning the ID of the final folder.

    Args:
        service: Google Drive API service instance
        path: Folder path like "sub1/sub2/sub3"
        base_folder_id: ID of the base folder to start from

    Returns:
        The ID of the final folder in the path
    """
    current_parent_id = base_folder_id

    # Split path and create each folder in sequence
    for folder_name in path.split("/"):
        if folder_name:  # Skip empty strings
            current_parent_id = find_or_create_folder(
                service, folder_name, current_parent_id
            )

    return current_parent_id


def _get_or_create_parent_folder_id(
    service, filename_with_path: str, base_folder_id: str
) -> str:
    """Determine the parent folder ID for the file upload.

    If a path is included in the filename, this function ensures the folder
    structure exists and returns the ID of the immediate parent folder. Otherwise,
    it returns the base_folder_id.

    Args:
        service: Google Drive API service instance
        filename_with_path: The full path of the file, including directories
        base_folder_id: The ID of the base folder to start from

    Returns:
        The ID of the parent folder for the file upload
    """
    dir_path = os.path.dirname(filename_with_path)
    if dir_path:
        return ensure_folder_path(service, dir_path, base_folder_id)
    return base_folder_id


def _perform_upload(
    service, filename: str, content: bytes, parent_folder_id: str, mime_type: str
) -> str:
    """Upload the file content to the specified parent folder.

    Args:
        service: Google Drive API service instance
        filename: The name of the file to be created
        content: The file content as bytes
        parent_folder_id: The ID of the folder where the file will be uploaded
        mime_type: The MIME type of the file

    Returns:
        The ID of the uploaded file
    """
    bytes_content = BytesIO(content)
    file_metadata = {"name": filename, "parents": [parent_folder_id]}
    media = MediaIoBaseUpload(bytes_content, mimetype=mime_type, resumable=True)

    uploaded_file = (
        service.files()  # type: ignore
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    return uploaded_file["id"]


def upload_file_with_path(
    service,
    filename_with_path: str,
    content: bytes,
    base_folder_id: str,
    mime_type: str,
) -> str:
    """Upload a file to Google Drive, creating nested folders as needed.

    Args:
        service: Google Drive API service instance
        filename_with_path: Path like "sub1/sub2/example.txt"
        content: File content as bytes
        base_folder_id: ID of the base folder
        mime_type: MIME type of the file

    Returns:
        The ID of the uploaded file
    """
    parent_folder_id = _get_or_create_parent_folder_id(
        service, filename_with_path, base_folder_id
    )

    filename = os.path.basename(filename_with_path)

    return _perform_upload(service, filename, content, parent_folder_id, mime_type)
