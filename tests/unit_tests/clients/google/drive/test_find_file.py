from datetime import datetime

from sebastian.clients.google.drive.client import GoogleDriveClient

from .fake_drive_service import FakeDriveService, file, folder

_BASE_FOLDER_ID = "base-folder-id"


def _client(service: FakeDriveService) -> GoogleDriveClient:
    """A client wired to the fake service instead of a built API resource."""
    client = GoogleDriveClient.__new__(GoogleDriveClient)
    client._service = service  # pyright: ignore[reportAttributeAccessIssue]
    return client


def test_find_file_returns_the_id_of_a_file_in_the_base_folder():
    service = FakeDriveService([file("Rechnung.pdf", "file-rechnung")])

    assert _client(service).find_file("Rechnung.pdf", _BASE_FOLDER_ID) == "file-rechnung"


def test_find_file_returns_none_when_the_file_is_absent():
    service = FakeDriveService([file("Andere.pdf", "file-andere")])

    assert _client(service).find_file("Rechnung.pdf", _BASE_FOLDER_ID) is None


def test_find_file_walks_each_folder_segment_of_a_nested_path():
    service = FakeDriveService(
        [
            folder("Miete", "folder-miete"),
            folder("2024", "folder-2024", parent_id="folder-miete"),
            file("Rechnung.pdf", "file-rechnung", parent_id="folder-2024"),
        ]
    )

    assert (
        _client(service).find_file("Miete/2024/Rechnung.pdf", _BASE_FOLDER_ID)
        == "file-rechnung"
    )


def test_find_file_returns_none_when_a_folder_segment_is_missing():
    service = FakeDriveService([file("Rechnung.pdf", "file-rechnung")])

    assert _client(service).find_file("Fehlt/Rechnung.pdf", _BASE_FOLDER_ID) is None


def test_find_file_escapes_quotes_in_names():
    # Portal names really can contain apostrophes (see the walk tests).
    service = FakeDriveService([file("Mieterh's.pdf", "file-quote")])

    assert _client(service).find_file("Mieterh's.pdf", _BASE_FOLDER_ID) == "file-quote"


def test_find_file_answers_duplicated_names_deterministically():
    # The old duplicate bug left several folders "Miete" and several files
    # "Rechnung.pdf" behind. The rule is documented in find_file.py: the oldest
    # createdTime wins, ties broken by the smallest id. Nothing is deleted.
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
            file(
                "Rechnung.pdf",
                "file-new",
                parent_id="folder-miete-old",
                created_time="2024-06-01T00:00:00.000Z",
            ),
            file(
                "Rechnung.pdf",
                "file-old",
                parent_id="folder-miete-old",
                created_time="2020-01-01T00:00:00.000Z",
            ),
        ]
    )
    client = _client(service)

    assert client.find_file("Miete/Rechnung.pdf", _BASE_FOLDER_ID) == "file-old"
    assert client.find_file("Miete/Rechnung.pdf", _BASE_FOLDER_ID) == "file-old"


def test_find_file_breaks_a_created_time_tie_with_the_smallest_id():
    service = FakeDriveService(
        [
            file("Rechnung.pdf", "file-b"),
            file("Rechnung.pdf", "file-a"),
        ]
    )

    assert _client(service).find_file("Rechnung.pdf", _BASE_FOLDER_ID) == "file-a"
