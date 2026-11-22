from sebastian.clients.google.drive.client import GoogleDriveClient
from sebastian.domain.gdrive import UploadFileRequest

from .fake_drive_service import FakeDriveService, folder

_BASE_FOLDER_ID = "base-folder-id"


def _client(service: FakeDriveService) -> GoogleDriveClient:
    client = GoogleDriveClient.__new__(GoogleDriveClient)
    client._service = service  # pyright: ignore[reportAttributeAccessIssue]
    return client


def test_upload_into_a_duplicated_folder_uses_the_same_candidate_as_find_file():
    # Same rule as the lookup: the oldest of the duplicate folders. Creating a
    # fresh duplicate, or uploading into the newer one, would make the next
    # find_file miss the file and duplicate it again.
    service = FakeDriveService(
        [
            folder(
                "Miete",
                "folder-miete-new",
                created_time="2024-06-01T00:00:00.000Z",
            ),
            folder(
                "Miete",
                "folder-miete-old",
                created_time="2020-01-01T00:00:00.000Z",
            ),
        ]
    )

    _client(service).upload_file(
        UploadFileRequest(
            filename="Miete/Rechnung.pdf",
            content=b"%PDF-1.7",
            folder_id=_BASE_FOLDER_ID,
        )
    )

    assert len(service.create_calls) == 1
    created = service.create_calls[0]["body"]
    assert created["name"] == "Rechnung.pdf"
    assert created["parents"] == ["folder-miete-old"]
    # The existing upload metadata is unchanged: name and parents only.
    assert "mimeType" not in created
