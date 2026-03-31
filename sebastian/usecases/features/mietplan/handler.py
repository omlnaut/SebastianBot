from dataclasses import dataclass
import logging
from datetime import timedelta

from sebastian.protocols.google_drive import IGoogleDriveClient, UploadFileRequest
from sebastian.protocols.mietplan import File, Folder, IMietplanClient
from sebastian.protocols.models import AllActor, SendMessage
from sebastian.shared.dates import is_within_timedelta
from sebastian.usecases.usecase_handler import UseCaseHandler


@dataclass
class Request:
    max_file_age: timedelta


class Handler(UseCaseHandler[Request]):
    def __init__(
        self,
        mietplan_client: IMietplanClient,
        google_drive_client: IGoogleDriveClient,
        gdrive_folder_id: str,
    ):
        self.mietplan_client = mietplan_client
        self.google_drive_client = google_drive_client
        self.gdrive_folder_id = gdrive_folder_id

    def handle(self, request: Request) -> AllActor:
        """
        Checks for new files in the mietplan source, and if they are newer than max_file_age,
        uploads them to Google Drive.

        Returns:
            AllActor: With send_messages containing success or error messages.
        """
        logging.info("Starting to process new mietplan files.")

        newly_uploaded_files = [
            self._process_new_file(file, folder)
            for file, folder in self._get_all_new_files(request.max_file_age)
        ]

        logging.info(
            f"Finished processing. Uploaded {len(newly_uploaded_files)} new files."
        )

        if not newly_uploaded_files:
            return AllActor(create_tasks=[], send_messages=[])

        message = _create_message(newly_uploaded_files)
        return AllActor(create_tasks=[], send_messages=[SendMessage(message=message)])

    def _process_new_file(self, file: File, folder: Folder) -> str:
        logging.info(f"  Found new file: {file.name}")
        file_content = self._download_file_from_mietplan(file)
        upload_path = self._upload_to_gdrive(file, folder, file_content)
        return upload_path

    def _get_all_new_files(self, max_file_age: timedelta) -> list[tuple[File, Folder]]:
        return [
            (file, folder)
            for folder in self.mietplan_client.walk_from_top_folder()
            for file in folder.files
            if is_within_timedelta(file.creation_date, max_file_age)
        ]

    def _download_file_from_mietplan(self, file: File) -> bytes:
        logging.info("    Downloading...")
        return self.mietplan_client.download_file(file.url)

    def _upload_to_gdrive(self, file: File, folder: Folder, content: bytes) -> str:
        upload_path = _build_upload_path(file, folder)
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
        return upload_path


def _create_message(uploaded_files: list[str]) -> str:
    message = "Found new mietplan files:\n" + "\n".join(
        [f"- {file}" for file in uploaded_files]
    )
    return message


def _build_upload_path(file: File, folder: Folder) -> str:
    return f"{'/'.join(folder.path)}/{file.name}".strip("/")
