from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel


class GmailLabel(Enum):
    """Enum mapping readable label names to Gmail label IDs. Fill in actual label IDs as needed."""

    ToRead = "Label_2648990123443534971"


@dataclass
class PdfAttachment:
    """Represents a PDF attachment with filename and data"""

    filename: str
    data: bytes


class FullMailResponse(BaseModel):
    id: str
    threadId: str
    labelIds: list[str]
    snippet: str
    raw_payload: dict
    sizeEstimate: int
    historyId: str
    internalDate: str
    content: str
