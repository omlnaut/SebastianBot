import logging
from datetime import datetime, timedelta

from sebastian.protocols.google_drive.models import UploadFileRequest
from sebastian.protocols.mietplan.models import File, Folder
from sebastian.protocols.google_drive import IGoogleDriveClient
from sebastian.protocols.mietplan import IMietplanClient
from sebastian.shared.Result import Result


class MietplanService:
    def __init__(
        self,
        mietplan_client: IMietplanClient,
        google_drive_client: IGoogleDriveClient,
        gdrive_folder_id: str,
    ):
        self.mietplan_client = mietplan_client
        self.google_drive_client = google_drive_client
        self.gdrive_folder_id = gdrive_folder_id

    def process_new_files(
        self, max_file_age: timedelta = timedelta(days=1)
    ) -> Result[list[str]]:
        """
        Checks for new files in the mietplan source, and if they are newer than max_file_age,
        uploads them to Google Drive.

        Returns:
            Result[list[str]]: A list of uploaded file paths on success, or an error message on failure.
        """
        try:
            logging.info("Starting to process new mietplan files.")

            newly_uploaded_files = []
            for file, folder in self._get_all_file_folder_pairs():
                if not self._is_new_file(file, max_file_age):
                    continue

                logging.info(f"  Found new file: {file.name}")
                file_content = self._download_file(file)
                upload_path = self._get_upload_path(file, folder)
                self._upload_to_gdrive(upload_path, file_content)
                newly_uploaded_files.append(upload_path)

            logging.info(
                f"Finished processing. Uploaded {len(newly_uploaded_files)} new files."
            )
            return Result.from_item(newly_uploaded_files)

        except Exception as e:
            logging.error(
                f"An error occurred during mietplan file processing: {e}", exc_info=True
            )
            return Result.from_item(errors=[str(e)])

    def _get_all_file_folder_pairs(self) -> list[tuple[File, Folder]]:
        return [
            (file, folder)
            for folder in self.mietplan_client.walk_from_top_folder()
            for file in folder.files
        ]

    def _is_new_file(self, file: File, max_age: timedelta) -> bool:
        return file.creation_date > datetime.now() - max_age

    def _download_file(self, file: File) -> bytes:
        logging.info("    Downloading...")
        return self.mietplan_client.download_file(file.url)

    def _get_upload_path(self, file: File, folder: Folder) -> str:
        return f"{'/'.join(folder.path)}/{file.name}".strip("/")

    def _upload_to_gdrive(self, upload_path: str, content: bytes):
        upload_request = UploadFileRequest(
            filename=upload_path,
            content=content,
            folder_id=self.gdrive_folder_id,
            mime_type="application/octet-stream",  # Assuming generic binary file
        )
        response = self.google_drive_client.upload_file(upload_request)
        logging.info(
            f"    Uploaded to Google Drive with file_id: {response.file_id} at path: {upload_path}"
        )
