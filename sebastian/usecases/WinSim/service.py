from datetime import datetime, timedelta, timezone

from sebastian.protocols.google_drive import IGoogleDriveClient, UploadFileRequest
from sebastian.shared.gmail.query_builder import GmailQueryBuilder

from .protocols import GmailClient


class WinSimService:
    """Service for handling WinSim invoice downloads and uploads to Google Drive."""

    def __init__(
        self,
        gmail_client: GmailClient,
        drive_client: IGoogleDriveClient,
        winsim_folder_id: str,
    ):
        self.gmail_client = gmail_client
        self.drive_client = drive_client
        self.winsim_folder_id = winsim_folder_id

    def process_recent_invoices(self, hours_back: int = 24) -> list[str]:
        """
        Fetch recent WinSim invoices and upload them to Google Drive.

        Args:
            hours_back: Number of hours to look back for new invoices (default: 24)

        Returns:
            List of uploaded file IDs
        """
        pdfs = self._download_pdf_attachments(hours_back)

        uploaded_file_ids, _ = self._try_upload_files(pdfs)

        return uploaded_file_ids

    def _try_upload_files(self, pdfs):
        uploaded_file_ids: list[str] = []
        errors: list[str] = []

        for pdf in pdfs:
            try:
                # Generate filename in format: yyyy-mm_winsim.pdf
                filename = self._generate_filename()

                upload_request = UploadFileRequest(
                    content=pdf.data,
                    filename=filename,
                    folder_id=self.winsim_folder_id,
                    mime_type="application/pdf",
                )

                response = self.drive_client.upload_file(upload_request)
                uploaded_file_ids.append(response.file_id)
            except Exception as e:
                errors.append(f"Error uploading {pdf.filename}: {str(e)}")
        return uploaded_file_ids, errors

    def _download_pdf_attachments(self, hours_back: int):
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        query = (
            GmailQueryBuilder()
            .from_email("no-reply@winsim.de")
            .has_attachment("pdf")
            .after_date(time_threshold)
            .build()
        )
        mails = self.gmail_client.fetch_mails(query)

        pdfs = [
            pdf
            for mail in mails
            for pdf in self.gmail_client.download_pdf_attachments(mail)
        ]
        return pdfs

    def _generate_filename(self) -> str:
        """
        Generate filename in format: yyyy-mm_winsim.pdf based on current date.

        Returns:
            Formatted filename
        """
        current_date = datetime.now()
        first_of_current_month = current_date.replace(day=1)
        previous_month = first_of_current_month - timedelta(days=1)
        return f"{previous_month.year}-{previous_month.month:02d}_winsim.pdf"
