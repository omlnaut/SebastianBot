import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Sequence

from sebastian.domain.gdrive import UploadFileRequest
from sebastian.domain.mietplan import MietplanFile, MietplanFolder
from sebastian.domain.side_effect import SideEffect, SendMessage
from sebastian.usecases.shared.dates import is_within_timedelta
from sebastian.usecases.usecase_handler import UseCaseHandler

from .protocols import IGoogleDriveClient, IMietplanClient

_MIME_TYPE = "application/octet-stream"


@dataclass
class Request:
    """A sync request.

    ``max_file_age is None`` means "no age limit": every file in the whole
    webdepot is in scope. It never means "no files". The timer keeps
    ``timedelta(days=1)``.
    """

    max_file_age: timedelta | None


@dataclass
class SyncReport:
    """What one run wrote, split by whether the Drive path already existed.

    ``uploaded``: the path did not exist in Drive and was created.
    ``replaced``: the path existed and that file's content was updated in place.

    Plain additive value object -- the manual resync route (#127) extends it
    with its own fields and reads it from the handler.
    """

    uploaded: list[str] = field(default_factory=list)
    replaced: list[str] = field(default_factory=list)


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
        self.report = SyncReport()

    def handle(self, request: Request) -> Sequence[SideEffect]:
        """
        Syncs mietplan files to Google Drive: downloads every file in scope and
        writes it to its path, replacing the existing Drive file in place when
        that path is already there and creating it when it is not.

        Every file in scope is written on every run -- no skip cache, no marker.
        Nothing is ever deleted.

        Returns:
            Sequence[SideEffect]: Returns a list of base actor events (e.g. SendMessage).
        """
        logging.info("Starting to process new mietplan files.")

        self.report = SyncReport()

        written_files = [
            self._sync_file(file, folder)
            for file, folder in self._get_files_in_scope(request.max_file_age)
        ]

        logging.info(
            f"Finished processing. Wrote {len(written_files)} files "
            f"({len(self.report.uploaded)} uploaded, "
            f"{len(self.report.replaced)} replaced)."
        )

        if not written_files:
            return []

        message = _create_message(written_files)
        return [SendMessage(message=message)]

    def _sync_file(self, file: MietplanFile, folder: MietplanFolder) -> str:
        logging.info(f"  Found file: {file.name}")
        content = self._download_file_from_mietplan(file)
        upload_path = _build_upload_path(file, folder)

        existing_file_id = self.google_drive_client.find_file(
            upload_path, self.gdrive_folder_id
        )
        if existing_file_id is None:
            self._create_file(upload_path, content)
            self.report.uploaded.append(upload_path)
        else:
            self._replace_file(existing_file_id, content)
            self.report.replaced.append(upload_path)

        return upload_path

    def _get_files_in_scope(
        self, max_file_age: timedelta | None
    ) -> list[tuple[MietplanFile, MietplanFolder]]:
        return [
            (file, folder)
            for folder in self.mietplan_client.walk_from_top_folder()
            for file in folder.files
            if max_file_age is None
            or is_within_timedelta(file.creation_date, max_file_age)
        ]

    def _download_file_from_mietplan(self, file: MietplanFile) -> bytes:
        logging.info("    Downloading...")
        return self.mietplan_client.download_file(file.url)

    def _create_file(self, upload_path: str, content: bytes) -> None:
        upload_request = UploadFileRequest(
            filename=upload_path,
            content=content,
            folder_id=self.gdrive_folder_id,
            mime_type=_MIME_TYPE,
        )
        response = self.google_drive_client.upload_file(upload_request)
        logging.info(
            f"    Uploaded to Google Drive with file_id: {response.file_id} "
            f"at path: {upload_path}"
        )

    def _replace_file(self, file_id: str, content: bytes) -> None:
        self.google_drive_client.replace_file(file_id, content, _MIME_TYPE)
        logging.info(f"    Replaced Google Drive file_id: {file_id}")


def _create_message(uploaded_files: list[str]) -> str:
    message = "Found new mietplan files:\n" + "\n".join(
        [f"- {file}" for file in uploaded_files]
    )
    return message


def _build_upload_path(file: MietplanFile, folder: MietplanFolder) -> str:
    return f"{'/'.join(folder.path)}/{file.name}".strip("/")
