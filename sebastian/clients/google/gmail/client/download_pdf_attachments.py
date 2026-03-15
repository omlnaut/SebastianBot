from sebastian.clients.google.gmail.client.service_wrapper import GmailServiceWrapper
from sebastian.domain.gmail import FullMailResponse, PdfAttachment


def download_pdf_attachments_from_messages(
    service: GmailServiceWrapper, mail: FullMailResponse
) -> list[PdfAttachment]:
    """Download all PDF attachments from a list of messages"""
    pdf_attachments: list[PdfAttachment] = []

    for pdf_part in mail.pdf_parts:
        pdf_bytes = service.download_pdf_attachment(
            mail.id, pdf_part.body.attachment_id
        )
        pdf_attachments.append(
            PdfAttachment(filename=pdf_part.filename, data=pdf_bytes)
        )

    return pdf_attachments
