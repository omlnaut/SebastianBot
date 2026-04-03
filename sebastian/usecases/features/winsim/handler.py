from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging

from sebastian.protocols.google_drive import UploadFileRequest
from sebastian.protocols.models import BaseActorEvent, SendMessage
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.usecases.usecase_handler import UseCaseHandler

from .protocols import GmailClient, GoogleDriveClient

__all__ = ["Request", "Handler", "GmailClient", "GoogleDriveClient"]


@dataclass
class Request:
    time_back: timedelta = timedelta(hours=24)


class Handler(UseCaseHandler[Request]):
    def __init__(
        self,
        gmail_client: GmailClient,
        drive_client: GoogleDriveClient,
        winsim_folder_id: str,
    ):
        self._gmail_client = gmail_client
        self._drive_client = drive_client
        self._winsim_folder_id = winsim_folder_id

    def handle(self, request: Request) -> list[BaseActorEvent]:
        time_threshold = datetime.now(timezone.utc) - request.time_back
        query = (
            GmailQueryBuilder()
            .from_email("no-reply@winsim.de")
            .has_attachment("pdf")
            .after_date(time_threshold)
            .build()
        )
        mails = self._gmail_client.fetch_mails(query)
        logging.info(f"Fetched {len(mails)} WinSim mails")

        pdfs = [
            pdf
            for mail in mails
            for pdf in self._gmail_client.download_pdf_attachments(mail)
        ]

        uploaded_file_ids: list[str] = []
        errors: list[SendMessage] = []

        for pdf in pdfs:
            try:
                filename = _generate_filename()
                upload_request = UploadFileRequest(
                    content=pdf.data,
                    filename=filename,
                    folder_id=self._winsim_folder_id,
                    mime_type="application/pdf",
                )
                response = self._drive_client.upload_file(upload_request)
                uploaded_file_ids.append(response.file_id)
                logging.info(f"Uploaded {pdf.filename} as {filename} (id: {response.file_id})")
            except Exception as e:
                errors.append(SendMessage(message=f"Error uploading {pdf.filename}: {str(e)}"))

        messages = errors
        if n_uploads := len(uploaded_file_ids):
            messages.append(
                SendMessage(
                    message=f"📄 WinSim: Uploaded {n_uploads} invoice(s) to Google Drive"
                )
            )

        return messages


def _generate_filename() -> str:
    first_of_current_month = datetime.now().replace(day=1)
    previous_month = first_of_current_month - timedelta(days=1)
    return f"{previous_month.year}-{previous_month.month:02d}_winsim.pdf"
