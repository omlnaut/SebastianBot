# pyright: basic
from pydantic import BaseModel, ConfigDict, Field

from sebastian.clients.google.gmail.client.service_wrapper import GmailServiceWrapper
from sebastian.domain.gmail import FullMailResponse, PdfAttachment


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


def download_pdf_attachments_from_messages(
    service: GmailServiceWrapper, mail: FullMailResponse
) -> list[PdfAttachment]:
    """Download all PDF attachments from a list of messages"""
    pdf_attachments: list[PdfAttachment] = []

    pdf_parts = _extract_pdf_parts(mail)
    for pdf_part in pdf_parts:
        pdf_bytes = service.download_pdf_attachment(
            mail.id, pdf_part.body.attachment_id
        )
        pdf_attachments.append(
            PdfAttachment(filename=pdf_part.filename, data=pdf_bytes)
        )

    return pdf_attachments
