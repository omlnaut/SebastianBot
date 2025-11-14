from pydantic import BaseModel


class UploadFileRequest(BaseModel):
    """Request model for uploading a file to Google Drive."""

    filename: str
    content: bytes
    folder_id: str
    mime_type: str = "application/octet-stream"


class UploadFileResponse(BaseModel):
    """Response model for file upload to Google Drive."""

    file_id: str
