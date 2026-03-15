from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class GmailLabel(Enum):
    """Enum mapping readable label names to Gmail label IDs. Fill in actual label IDs as needed."""

    ToRead = "Label_2648990123443534971"


@dataclass
class PdfAttachment:
    """Represents a PDF attachment with filename and data"""

    filename: str
    data: bytes


class PdfMessageBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    attachment_id: str = Field(alias="attachmentId")
    size: int


class PdfMessagePart(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: str
    mime_type: str = Field(alias="mimeType")
    body: PdfMessageBody


class FullMailResponse(BaseModel):
    id: str
    threadId: str
    labelIds: list[str]
    snippet: str
    sizeEstimate: int
    historyId: str
    internalDate: str
    content: str
    pdf_parts: list[PdfMessagePart]
