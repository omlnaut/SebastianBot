import base64
from io import BytesIO

from pydantic import BaseModel, ConfigDict, Field

from ..models import FullMailResponse, PdfAttachment


class PdfMessageBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    attachment_id: str = Field(alias="attachmentId")
    size: int


class PdfMessagePart(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: str
    mime_type: str = Field(alias="mimeType")
    body: PdfMessageBody


def _extract_pdf_parts(message: FullMailResponse) -> list[PdfMessagePart]:
    """Extract PDF attachment parts from a message"""
    if "parts" not in message.raw_payload:
        return []

    parts = message.raw_payload["parts"]
    pdf_parts = [part for part in parts if part.get("mimeType") == "application/pdf"]
    return [PdfMessagePart.model_validate(part) for part in pdf_parts]


def _download_pdf_attachment(service, message_id: str, attachment_id: str) -> bytes:
    """Download a single PDF attachment and return as BytesIO"""
    attachment = (
        service.users()  # type: ignore
        .messages()
        .attachments()
        .get(
            userId="me",
            messageId=message_id,
            id=attachment_id,
        )
        .execute()
    )

    if not attachment:
        raise ValueError("Attachment not found")

    pdf_bytes = base64.urlsafe_b64decode(attachment["data"])
    return pdf_bytes


def download_pdf_attachments_from_messages(
    service, messages: list[FullMailResponse]
) -> list[PdfAttachment]:
    """Download all PDF attachments from a list of messages"""
    pdf_attachments: list[PdfAttachment] = []

    for message in messages:
        pdf_parts = _extract_pdf_parts(message)
        for pdf_part in pdf_parts:
            pdf_bytes = _download_pdf_attachment(
                service, message.id, pdf_part.body.attachment_id
            )
            pdf_attachments.append(
                PdfAttachment(filename=pdf_part.filename, data=pdf_bytes)
            )

    return pdf_attachments
