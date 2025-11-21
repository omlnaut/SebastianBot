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
    # Split the path into directory and filename
    dir_path = os.path.dirname(filename_with_path)
    filename = os.path.basename(filename_with_path)

    # Navigate/create the folder structure if path is provided
    if dir_path:
        parent_folder_id = ensure_folder_path(service, dir_path, base_folder_id)
    else:
        parent_folder_id = base_folder_id

    # Upload the file to the final folder
    bytes_content = BytesIO(content)
    file_metadata = {"name": filename, "parents": [parent_folder_id]}
    media = MediaIoBaseUpload(bytes_content, mimetype=mime_type, resumable=True)

    uploaded_file = (
        service.files()  # type: ignore
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    return uploaded_file["id"]
