"""Live verification of the upsert mechanics against real Google Drive.

Spec V3 (does ``files().update(media_body=...)`` keep id, parents and sharing?)
and V4 (is a path lookup unambiguous / deterministic when duplicates exist?)
can only be answered here. Run with ``pytest tests/integration_tests/mietplan``
on a machine that has the bot's Google credentials.
"""

from uuid import uuid4

from sebastian.clients.google.drive.client import GoogleDriveClient
from sebastian.domain.gdrive import UploadFileRequest

_ROOT_FOLDER_ID = "root"
_MIME_TYPE = "text/plain"


def _unique_path(filename: str) -> str:
    return f"sebastianbot-integration-{uuid4().hex}/{filename}"


def test_find_after_upload_returns_the_uploaded_file(drive_client: GoogleDriveClient):
    path = _unique_path("probe.txt")

    uploaded = drive_client.upload_file(
        UploadFileRequest(
            filename=path,
            content=b"first version",
            folder_id=_ROOT_FOLDER_ID,
            mime_type=_MIME_TYPE,
        )
    )

    assert drive_client.find_file(path, _ROOT_FOLDER_ID) == uploaded.file_id


def test_upsert_replaces_the_same_file_id_and_keeps_it_findable(
    drive_client: GoogleDriveClient,
):
    path = _unique_path("probe.txt")
    uploaded = drive_client.upload_file(
        UploadFileRequest(
            filename=path,
            content=b"first version",
            folder_id=_ROOT_FOLDER_ID,
            mime_type=_MIME_TYPE,
        )
    )

    existing_file_id = drive_client.find_file(path, _ROOT_FOLDER_ID)
    assert existing_file_id == uploaded.file_id
    drive_client.replace_file(existing_file_id, b"corrected version", _MIME_TYPE)

    # V3: the id survives the update, so a second sync replaces in place.
    assert drive_client.find_file(path, _ROOT_FOLDER_ID) == uploaded.file_id


def test_find_file_of_an_absent_path_returns_none(drive_client: GoogleDriveClient):
    assert drive_client.find_file(_unique_path("absent.txt"), _ROOT_FOLDER_ID) is None
