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


@dataclass(frozen=True)
class ParsedAttachment:
    """An attachment discovered anywhere in a mail's part tree."""

    filename: str
    mime_type: str
    size: int
    attachment_id: str | None = None
    inline_data: bytes | None = None


@dataclass(frozen=True)
class ParsedMail:
    """A raw Gmail payload normalized into the fields a recall tool needs."""

    sender: str
    to: list[str]
    cc: list[str]
    subject: str
    date: str | None
    message_id: str | None
    references: str | None
    text_body: str | None
    html_body: str | None
    attachments: list[ParsedAttachment]


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


@dataclass(frozen=True)
class AttachmentInfo:
    """Attachment metadata as surfaced by a search hit."""

    filename: str
    mime_type: str
    size: int


@dataclass(frozen=True)
class WrittenAttachment:
    """One attachment written to disk."""

    path: str
    size: int


@dataclass(frozen=True)
class MailHit:
    """The shared hit shape used by both search results and `show`."""

    id: str
    thread_id: str
    sender: str
    to: list[str]
    cc: list[str]
    subject: str
    date: str | None
    internal_date: str
    labels: list[str]
    label_ids: list[str]
    snippet: str
    size_estimate: int
    has_attachments: bool
    attachments: list[AttachmentInfo]


@dataclass(frozen=True)
class SearchPage:
    """One page of a metadata-only search."""

    hits: list[MailHit]
    next_page_token: str | None
    result_size_estimate: int | None


@dataclass(frozen=True)
class ShownMail:
    """One mail read in full: the shared hit shape plus its rendered body."""

    hit: MailHit
    body: str
    body_format: str
    truncated: bool


@dataclass(frozen=True)
class Label:
    """A Gmail label with its id resolved to a readable name."""

    id: str
    name: str
    type: str | None
    visibility: str | None


@dataclass(frozen=True)
class OutgoingAttachment:
    """One file to attach to an outgoing draft, already read from disk."""

    path: str
    filename: str
    mime_type: str
    size: int
    data: bytes


@dataclass(frozen=True)
class DraftRequest:
    """Everything one composed draft needs, with recipients already validated."""

    to: list[str]
    cc: list[str]
    bcc: list[str]
    subject: str
    body: str
    attachments: list[OutgoingAttachment]
    thread_id: str | None = None
    in_reply_to: str | None = None
    references: str | None = None


@dataclass(frozen=True)
class ComposedDraft:
    """A draft rendered to MIME, ready to hand to the Gmail API."""

    raw: bytes
    encoded: str
    encoded_bytes: int
    request: DraftRequest


@dataclass(frozen=True)
class CreatedDraft:
    """The identifiers Gmail returned for a created draft."""

    draft_id: str
    message_id: str
    thread_id: str


@dataclass(frozen=True)
class ReplyContext:
    """The few fields of an existing mail that a reply draft is derived from."""

    thread_id: str
    sender: str
    to: list[str]
    cc: list[str]
    subject: str
    message_id_header: str | None
    references: str | None


@dataclass(frozen=True)
class ReplyTarget:
    """Recipients and threading headers derived from a mail being replied to."""

    to: list[str]
    cc: list[str]
    subject: str
    thread_id: str
    in_reply_to: str | None
    references: str | None
