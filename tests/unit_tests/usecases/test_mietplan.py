from datetime import date, datetime, time, timedelta
from typing import Generator

from sebastian.domain.gdrive import UploadFileRequest, UploadFileResponse
from sebastian.domain.mietplan import MietplanFile, MietplanFolder
from sebastian.domain.side_effect import SendMessage, SideEffect
from sebastian.usecases.features.mietplan.handler import Handler, Request

_GDRIVE_FOLDER_ID = "gdrive-folder-id"


class _FakeMietplanClient:
    def __init__(self, folders: list[MietplanFolder], contents: dict[str, bytes]):
        self._folders = folders
        self._contents = contents
        self.downloads: list[str] = []

    def walk_from_top_folder(self) -> Generator[MietplanFolder, None, None]:
        yield from self._folders

    def download_file(self, download_path: str) -> bytes:
        self.downloads.append(download_path)
        return self._contents[download_path]


class _FakeGoogleDriveClient:
    def __init__(self) -> None:
        self.uploads: list[UploadFileRequest] = []

    def upload_file(self, request: UploadFileRequest) -> UploadFileResponse:
        self.uploads.append(request)
        return UploadFileResponse(file_id=f"file-{len(self.uploads)}")


def _at(day: date, hour: int = 12) -> datetime:
    return datetime.combine(day, time(hour=hour))


def _file(name: str, url: str, creation_date: datetime | None = None) -> MietplanFile:
    return MietplanFile(
        creation_date=creation_date or _at(date.today()),
        name=name,
        url=url,
    )


def _folder(
    path: list[str],
    files: list[MietplanFile],
    folder_id: str = "folder-id",
) -> MietplanFolder:
    return MietplanFolder(id=folder_id, path=path, files=files)


def _handle(
    folders: list[MietplanFolder],
    contents: dict[str, bytes] | None = None,
    max_file_age: timedelta = timedelta(days=1),
) -> tuple[list[SideEffect], _FakeMietplanClient, _FakeGoogleDriveClient]:
    mietplan = _FakeMietplanClient(folders, contents or {})
    drive = _FakeGoogleDriveClient()
    handler = Handler(
        mietplan_client=mietplan,
        google_drive_client=drive,
        gdrive_folder_id=_GDRIVE_FOLDER_ID,
    )
    result = handler.handle(Request(max_file_age=max_file_age))
    return list(result), mietplan, drive


def test_age_filter_processes_only_files_inside_the_window():
    today = date.today()
    files = [
        _file("today.pdf", url="/Konto/today.pdf", creation_date=_at(today)),
        _file(
            "yesterday.pdf",
            url="/Konto/yesterday.pdf",
            creation_date=_at(today - timedelta(days=1), hour=0),
        ),
        _file(
            "two-days-ago.pdf",
            url="/Konto/two-days-ago.pdf",
            creation_date=_at(today - timedelta(days=2), hour=23),
        ),
        _file(
            "tomorrow.pdf",
            url="/Konto/tomorrow.pdf",
            creation_date=_at(today + timedelta(days=1), hour=0),
        ),
    ]

    _, mietplan, _ = _handle(
        [_folder(["Konto"], files)],
        {file.url: file.name.encode() for file in files},
    )

    # Lower bound is inclusive (yesterday at 00:00) and the upper bound is today
    # (tomorrow is dropped), both compared as dates rather than instants.
    assert mietplan.downloads == ["/Konto/today.pdf", "/Konto/yesterday.pdf"]


def test_upload_path_joins_folder_path_and_filename():
    _, _, drive = _handle(
        [_folder(["Miete", "2024"], [_file("Rechnung.pdf", url="/u/rechnung")])],
        {"/u/rechnung": b"rechnung"},
    )

    assert [upload.filename for upload in drive.uploads] == [
        "Miete/2024/Rechnung.pdf"
    ]


def test_upload_path_of_a_root_level_folder_has_no_leading_slash():
    _, _, drive = _handle(
        [_folder([], [_file("Rechnung.pdf", url="/u/rechnung")])],
        {"/u/rechnung": b"rechnung"},
    )

    assert [upload.filename for upload in drive.uploads] == ["Rechnung.pdf"]


def test_upload_path_strips_an_empty_leading_segment():
    _, _, drive = _handle(
        [_folder(["", "Miete", "2024"], [_file("Rechnung.pdf", url="/u/rechnung")])],
        {"/u/rechnung": b"rechnung"},
    )

    assert [upload.filename for upload in drive.uploads] == [
        "Miete/2024/Rechnung.pdf"
    ]


def test_upload_path_of_a_trailing_empty_segment_keeps_a_double_slash():
    # Characterization of today's behaviour: only leading and trailing slashes
    # are stripped, so an empty trailing folder segment survives as "//"
    # immediately before the filename.
    _, _, drive = _handle(
        [_folder(["Miete", "2024", ""], [_file("Rechnung.pdf", url="/u/rechnung")])],
        {"/u/rechnung": b"rechnung"},
    )

    assert [upload.filename for upload in drive.uploads] == [
        "Miete/2024//Rechnung.pdf"
    ]


def test_send_message_lists_uploaded_paths_in_walk_order():
    folders = [
        _folder(
            ["Miete", "2024"],
            [
                _file("a.pdf", url="/u/a"),
                _file("b.pdf", url="/u/b"),
            ],
            folder_id="folder-miete",
        ),
        _folder(["Konto"], [_file("c.pdf", url="/u/c")], folder_id="folder-konto"),
    ]

    result, _, _ = _handle(folders, {"/u/a": b"a", "/u/b": b"b", "/u/c": b"c"})

    assert result == [
        SendMessage(
            message=(
                "Found new mietplan files:\n"
                "- Miete/2024/a.pdf\n"
                "- Miete/2024/b.pdf\n"
                "- Konto/c.pdf"
            )
        )
    ]


def test_no_side_effects_when_no_file_matches_the_window():
    old = date.today() - timedelta(days=5)
    folders = [
        _folder(
            ["Konto"],
            [_file("old.pdf", url="/u/old", creation_date=_at(old))],
        )
    ]

    result, mietplan, drive = _handle(folders, {"/u/old": b"old"})

    assert result == []
    assert mietplan.downloads == []
    assert drive.uploads == []


def test_no_side_effects_when_the_walk_finds_no_folders():
    result, mietplan, drive = _handle([])

    assert result == []
    assert mietplan.downloads == []
    assert drive.uploads == []


def test_each_selected_file_is_downloaded_by_url_and_uploaded_with_its_bytes():
    folders = [
        _folder(
            ["Miete"],
            [
                _file("a.pdf", url="/Miete/a.pdf"),
                _file("b.pdf", url="/Miete/b.pdf"),
            ],
        )
    ]
    contents = {"/Miete/a.pdf": b"%PDF-1.7 a", "/Miete/b.pdf": b"%PDF-1.7 b"}

    _, mietplan, drive = _handle(folders, contents)

    assert mietplan.downloads == ["/Miete/a.pdf", "/Miete/b.pdf"]
    assert drive.uploads == [
        UploadFileRequest(
            filename="Miete/a.pdf",
            content=b"%PDF-1.7 a",
            folder_id=_GDRIVE_FOLDER_ID,
            mime_type="application/octet-stream",
        ),
        UploadFileRequest(
            filename="Miete/b.pdf",
            content=b"%PDF-1.7 b",
            folder_id=_GDRIVE_FOLDER_ID,
            mime_type="application/octet-stream",
        ),
    ]
