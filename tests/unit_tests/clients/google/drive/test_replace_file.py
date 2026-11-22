from sebastian.clients.google.drive.client import GoogleDriveClient

from .fake_drive_service import FakeDriveService, file, media_bytes


def _client(service: FakeDriveService) -> GoogleDriveClient:
    client = GoogleDriveClient.__new__(GoogleDriveClient)
    client._service = service  # pyright: ignore[reportAttributeAccessIssue]
    return client


def test_replace_file_updates_the_content_of_the_existing_file_id():
    service = FakeDriveService([file("Rechnung.pdf", "file-rechnung")])

    _client(service).replace_file(
        "file-rechnung", b"%PDF-1.7 corrected", "application/pdf"
    )

    assert not service.create_calls
    assert len(service.update_calls) == 1
    call = service.update_calls[0]
    assert call["fileId"] == "file-rechnung"
    assert call["fields"] == "id"
    assert media_bytes(call["media_body"]) == b"%PDF-1.7 corrected"
    assert call["media_body"].mimetype() == "application/pdf"


def test_replace_file_sends_no_metadata_body_so_name_and_parents_survive():
    service = FakeDriveService([file("Rechnung.pdf", "file-rechnung")])

    _client(service).replace_file("file-rechnung", b"content", "text/plain")

    assert service.update_calls[0]["body"] is None
