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
    ``timedelta(days=1)`` and is the only caller without an explicit choice, so
    the field stays required: an accidental whole-webdepot run must be spelled
    out.

    ``folder`` limits the run to that folder path prefix, matched segment by
    segment (``Archiv`` covers ``Archiv`` and ``Archiv/2019``, not ``Archiv2``).
    ``None`` or empty means every folder.

    ``dry_run`` classifies every file in scope exactly like a real run but
    downloads and writes nothing.
    """

    max_file_age: timedelta | None
    folder: str | None = None
    dry_run: bool = False


@dataclass
class SyncFailure:
    """A file that could not be synced, and the error it raised.

    ``path`` is the path the file would have been written to, so a failure is
    addressable exactly like an ``uploaded`` or ``replaced`` entry.
    """

    path: str
    error: str


@dataclass
class SyncReport:
    """What one run did, split by whether the Drive path already existed.

    ``uploaded``: the path did not exist in Drive and was created.
    ``replaced``: the path existed and that file's content was updated in place.
    ``failed``: files that raised; they do not abort the run.
    ``scanned_folders``: folders the walk visited, in scope or not.

    Plain additive value object -- the manual resync route (#127) serialises it.
    """

    uploaded: list[str] = field(default_factory=list)
    replaced: list[str] = field(default_factory=list)
    failed: list[SyncFailure] = field(default_factory=list)
    scanned_folders: int = 0


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

        written_files: list[str] = []
        for file, folder in self._get_files_in_scope(request):
            written = self._sync_file(file, folder, request.dry_run)
            if written is not None:
                written_files.append(written)

        logging.info(
            f"Finished processing. Wrote {len(written_files)} files "
            f"({len(self.report.uploaded)} uploaded, "
            f"{len(self.report.replaced)} replaced)."
        )

        if request.dry_run or (not written_files and not self.report.failed):
            return []

        message = _create_message(written_files, self.report.failed)
        return [SendMessage(message=message)]

    def _sync_file(
        self, file: MietplanFile, folder: MietplanFolder, dry_run: bool
    ) -> str | None:
        """Sync one file; return its path, or ``None`` when it failed.

        A failure is recorded on the report and never propagated: one broken
        file must not cost the rest of the run.
        """
        logging.info(f"  Found file: {file.name}")
        upload_path = _build_upload_path(file, folder)

        try:
            if dry_run:
                # Same lookup as below, so the classification is identical;
                # nothing is downloaded or written.
                self._record_outcome(
                    upload_path, self._find_existing_file(upload_path)
                )
                return upload_path

            content = self._download_file_from_mietplan(file)
            existing_file_id = self._find_existing_file(upload_path)
            if existing_file_id is None:
                self._create_file(upload_path, content)
            else:
                self._replace_file(existing_file_id, content)
            self._record_outcome(upload_path, existing_file_id)
        except Exception as error:
            logging.exception(f"    Failed to sync {upload_path}: {error}")
            self.report.failed.append(SyncFailure(path=upload_path, error=str(error)))
            return None

        return upload_path

    def _find_existing_file(self, upload_path: str) -> str | None:
        return self.google_drive_client.find_file(upload_path, self.gdrive_folder_id)

    def _record_outcome(
        self, upload_path: str, existing_file_id: str | None
    ) -> None:
        if existing_file_id is None:
            self.report.uploaded.append(upload_path)
        else:
            self.report.replaced.append(upload_path)

    def _get_files_in_scope(
        self, request: Request
    ) -> list[tuple[MietplanFile, MietplanFolder]]:
        prefix = _path_segments(request.folder)
        in_scope: list[tuple[MietplanFile, MietplanFolder]] = []
        for folder in self.mietplan_client.walk_from_top_folder():
            self.report.scanned_folders += 1
            if prefix and folder.path[: len(prefix)] != prefix:
                continue
            in_scope.extend(
                (file, folder)
                for file in folder.files
                if request.max_file_age is None
                or is_within_timedelta(file.creation_date, request.max_file_age)
            )
        return in_scope

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


def _create_message(
    written_files: list[str], failures: list[SyncFailure]
) -> str:
    lines = [f"- {file}" for file in written_files]
    if failures:
        lines.append("Failed:")
        lines.extend(
            f"- {failure.path}: {failure.error}" for failure in failures
        )
    return "Found new mietplan files:\n" + "\n".join(lines)


def _build_upload_path(file: MietplanFile, folder: MietplanFolder) -> str:
    return f"{'/'.join(folder.path)}/{file.name}".strip("/")


def _path_segments(prefix: str | None) -> list[str]:
    return [segment for segment in (prefix or "").split("/") if segment]
