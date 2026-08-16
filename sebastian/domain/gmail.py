from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field


@dataclass
class GmailLabel:
    name: str
    label_id: str


class GmailLabels:
    """Enum mapping readable label names to Gmail label IDs. Fill in actual label IDs as needed."""

    ToRead = GmailLabel(name="To Read", label_id="Label_2648990123443534971")
    Unread = GmailLabel(name="Unread", label_id="UNREAD")
    Processed = GmailLabel(
        name="Sebastian/Processed", label_id="Label_1123571739877587128"
    )


class GmailLabelResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    type: str | None = None
    message_list_visibility: str | None = Field(
        alias="messageListVisibility", default=None
    )
    label_list_visibility: str | None = Field(alias="labelListVisibility", default=None)


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
    is_read: bool
    subject: str
    from_email: str = ""
    snippet: str
    sizeEstimate: int
    historyId: str
    internalDate: str
    content: str
    pdf_parts: list[PdfMessagePart]

    def has_label(self, label: GmailLabel) -> bool:
        return label.label_id in self.labelIds

    def age(self, now: datetime | None = None) -> timedelta | None:
        if now is None:
            now = datetime.now(timezone.utc)

        timestamp = int(self.internalDate) / 1000

        received_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return now - received_at
