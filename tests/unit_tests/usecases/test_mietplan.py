from datetime import date, datetime, time, timedelta
from typing import Generator

from sebastian.domain.gdrive import UploadFileRequest, UploadFileResponse
from sebastian.domain.mietplan import MietplanFile, MietplanFolder
from sebastian.domain.side_effect import SendMessage, SideEffect
from sebastian.usecases.features.mietplan.handler import (
    Handler,
    Request,
    SyncFailure,
)

_GDRIVE_FOLDER_ID = "gdrive-folder-id"


class _FakeMietplanClient:
    def __init__(
        self,
        folders: list[MietplanFolder],
        contents: dict[str, bytes],
        fail_on: dict[str, Exception] | None = None,
    ):
        self._folders = folders
        self._contents = contents
        self._fail_on = fail_on or {}
        self.downloads: list[str] = []

    def walk_from_top_folder(self) -> Generator[MietplanFolder, None, None]:
        yield from self._folders

    def download_file(self, download_path: str) -> bytes:
        self.downloads.append(download_path)
        if download_path in self._fail_on:
            raise self._fail_on[download_path]
        return self._contents[download_path]


class _FakeGoogleDriveClient:
    def __init__(self, existing: list[str] | None = None) -> None:
        self.uploads: list[UploadFileRequest] = []
        # (filename_with_path, base_folder_id) per find_file call
        self.lookups: list[tuple[str, str]] = []
        # (file_id, content, mime_type) per replace_file call
        self.replacements: list[tuple[str, bytes, str]] = []
        self.deleted: list[str] = []
        self.contents: dict[str, bytes] = {}
        self._ids: dict[str, str] = {
            path: f"existing-{index}" for index, path in enumerate(existing or [])
        }
        self._next_id = 0

    def find_file(self, filename_with_path: str, base_folder_id: str) -> str | None:
        self.lookups.append((filename_with_path, base_folder_id))
        return self._ids.get(filename_with_path)

    def upload_file(self, request: UploadFileRequest) -> UploadFileResponse:
        self.uploads.append(request)
        self._next_id += 1
        file_id = f"file-{self._next_id}"
        self._ids[request.filename] = file_id
        self.contents[file_id] = request.content
        return UploadFileResponse(file_id=file_id)

    def replace_file(self, file_id: str, content: bytes, mime_type: str) -> None:
        self.replacements.append((file_id, content, mime_type))
        self.contents[file_id] = content

    def delete(self, file_id: str) -> None:
        self.deleted.append(file_id)

    def file_id(self, path: str) -> str:
        return self._ids[path]


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


def _make_handler(
    folders: list[MietplanFolder],
    contents: dict[str, bytes] | None = None,
    max_file_age: timedelta | None = timedelta(days=1),
    drive: _FakeGoogleDriveClient | None = None,
) -> tuple[Handler, _FakeMietplanClient, _FakeGoogleDriveClient]:
    mietplan = _FakeMietplanClient(folders, contents or {})
    drive = drive or _FakeGoogleDriveClient()
    handler = Handler(
        mietplan_client=mietplan,
        google_drive_client=drive,
        gdrive_folder_id=_GDRIVE_FOLDER_ID,
    )
    return handler, mietplan, drive


def _handle(
    folders: list[MietplanFolder],
    contents: dict[str, bytes] | None = None,
    max_file_age: timedelta | None = timedelta(days=1),
    drive: _FakeGoogleDriveClient | None = None,
    folder: str | None = None,
    dry_run: bool = False,
) -> tuple[list[SideEffect], _FakeMietplanClient, _FakeGoogleDriveClient]:
    handler, mietplan, drive = _make_handler(folders, contents, max_file_age, drive)
    result = handler.handle(
        Request(max_file_age=max_file_age, folder=folder, dry_run=dry_run)
    )
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


def test_each_selected_file_is_downloaded_by_url_and_created_when_absent():
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

    drive = _FakeGoogleDriveClient()

    _, mietplan, drive = _handle(folders, contents, drive=drive)

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

    # Flipped from the characterization of the old always-create behaviour: a
    # second run over the same paths updates instead of creating duplicates.
    _handle(folders, contents, drive=drive)

    assert len(drive.uploads) == 2
    assert drive.replacements == [
        (drive.file_id("Miete/a.pdf"), b"%PDF-1.7 a", "application/octet-stream"),
        (drive.file_id("Miete/b.pdf"), b"%PDF-1.7 b", "application/octet-stream"),
    ]


def test_second_sync_replaces_the_same_file_instead_of_creating_a_duplicate():
    folders = [_folder(["Miete"], [_file("a.pdf", url="/u/a")])]
    contents = {"/u/a": b"v1"}

    handler, _, drive = _make_handler(folders, contents)
    handler.handle(Request(max_file_age=timedelta(days=1)))
    file_id = drive.file_id("Miete/a.pdf")

    handler.handle(Request(max_file_age=timedelta(days=1)))

    assert len(drive.uploads) == 1, "the second run must not create a duplicate"
    assert drive.replacements == [(file_id, b"v1", "application/octet-stream")]
    assert drive.deleted == []
    assert handler.report.replaced == ["Miete/a.pdf"]
    assert handler.report.uploaded == []


def test_a_changed_portal_copy_replaces_the_content_of_the_same_drive_file():
    drive = _FakeGoogleDriveClient()
    folders = [_folder(["Miete"], [_file("a.pdf", url="/u/a")])]

    first, _, _ = _handle(folders, {"/u/a": b"%PDF-1.7 first"}, drive=drive)
    file_id = drive.file_id("Miete/a.pdf")

    _, mietplan, _ = _handle(folders, {"/u/a": b"%PDF-1.7 corrected"}, drive=drive)

    assert mietplan.downloads == ["/u/a"]
    assert drive.replacements == [
        (file_id, b"%PDF-1.7 corrected", "application/octet-stream")
    ]
    assert len(drive.uploads) == 1
    assert drive.contents[file_id] == b"%PDF-1.7 corrected"
    assert first  # the first run did write a message


def test_report_distinguishes_uploaded_from_replaced_in_walk_order():
    folders = [
        _folder(
            ["Miete"],
            [_file("a.pdf", url="/u/a"), _file("b.pdf", url="/u/b")],
        ),
        _folder(["Konto"], [_file("c.pdf", url="/u/c")], folder_id="folder-konto"),
    ]
    contents = {"/u/a": b"a", "/u/b": b"b", "/u/c": b"c"}
    drive = _FakeGoogleDriveClient(existing=["Miete/b.pdf"])

    handler, _, drive = _make_handler(folders, contents, drive=drive)
    handler.handle(Request(max_file_age=timedelta(days=1)))

    assert handler.report.uploaded == ["Miete/a.pdf", "Konto/c.pdf"]
    assert handler.report.replaced == ["Miete/b.pdf"]


def test_a_none_max_file_age_includes_the_whole_webdepot():
    old = date.today() - timedelta(days=400)
    folders = [
        _folder(
            ["Archiv"],
            [_file("old.pdf", url="/u/old", creation_date=_at(old))],
        )
    ]

    handler, mietplan, drive = _make_handler(
        folders, {"/u/old": b"old"}, max_file_age=None
    )
    result = handler.handle(Request(max_file_age=None))

    assert mietplan.downloads == ["/u/old"]
    assert [upload.filename for upload in drive.uploads] == ["Archiv/old.pdf"]
    assert handler.report.uploaded == ["Archiv/old.pdf"]
    assert result == [SendMessage(message="Found new mietplan files:\n- Archiv/old.pdf")]


_ARCHIV_TREE = [
    _folder(["Archiv"], [_file("own.pdf", url="/a/own")], folder_id="folder-archiv"),
    _folder(
        ["Archiv", "2019"],
        [_file("nested.pdf", url="/a/2019/nested")],
        folder_id="folder-2019",
    ),
    _folder(
        ["Archiv", "2019b"],
        [_file("sibling.pdf", url="/a/2019b/sibling")],
        folder_id="folder-2019b",
    ),
    _folder(["Archiv2"], [_file("other.pdf", url="/a2/other")], folder_id="f-a2"),
]
_ARCHIV_CONTENTS = {
    "/a/own": b"own",
    "/a/2019/nested": b"nested",
    "/a/2019b/sibling": b"sibling",
    "/a2/other": b"other",
}


def test_folder_scope_matches_whole_path_segments_not_prefixes_of_names():
    _, mietplan, _ = _handle(
        _ARCHIV_TREE, _ARCHIV_CONTENTS, max_file_age=None, folder="Archiv"
    )

    # "Archiv" selects the folder itself and its subfolders, never "Archiv2".
    assert mietplan.downloads == ["/a/own", "/a/2019/nested", "/a/2019b/sibling"]


def test_folder_scope_of_a_leaf_folder_includes_that_folder_s_own_files():
    _, mietplan, _ = _handle(
        _ARCHIV_TREE, _ARCHIV_CONTENTS, max_file_age=None, folder="Archiv/2019"
    )

    assert mietplan.downloads == ["/a/2019/nested"]


def test_empty_folder_scope_covers_every_folder():
    for folder in (None, "", "//"):
        _, mietplan, _ = _handle(
            _ARCHIV_TREE, _ARCHIV_CONTENTS, max_file_age=None, folder=folder
        )

        assert mietplan.downloads == [
            "/a/own",
            "/a/2019/nested",
            "/a/2019b/sibling",
            "/a2/other",
        ], folder


def test_dry_run_classifies_like_a_real_run_without_downloading_or_writing():
    folders = [
        _folder(
            ["Miete"],
            [_file("a.pdf", url="/u/a"), _file("b.pdf", url="/u/b")],
        ),
        _folder(["Konto"], [_file("c.pdf", url="/u/c")], folder_id="folder-konto"),
    ]
    contents = {"/u/a": b"a", "/u/b": b"b", "/u/c": b"c"}

    real_handler, _, real_drive = _make_handler(
        folders, contents, max_file_age=None, drive=_FakeGoogleDriveClient(["Miete/b.pdf"])
    )
    real_result = real_handler.handle(Request(max_file_age=None))

    dry_handler, dry_mietplan, dry_drive = _make_handler(
        folders, contents, max_file_age=None, drive=_FakeGoogleDriveClient(["Miete/b.pdf"])
    )
    dry_result = dry_handler.handle(Request(max_file_age=None, dry_run=True))

    # Same classification, from the same Drive path lookups, in walk order.
    assert dry_drive.lookups == real_drive.lookups
    assert dry_handler.report.uploaded == real_handler.report.uploaded == [
        "Miete/a.pdf",
        "Konto/c.pdf",
    ]
    assert dry_handler.report.replaced == real_handler.report.replaced == ["Miete/b.pdf"]
    assert dry_handler.report.failed == real_handler.report.failed == []

    # ... but nothing crosses the wire: no download, no write, no Telegram.
    assert dry_mietplan.downloads == []
    assert dry_drive.uploads == []
    assert dry_drive.replacements == []
    assert dry_drive.contents == {}
    assert dry_result == []
    assert real_result == [
        SendMessage(
            message=(
                "Found new mietplan files:\n"
                "- Miete/a.pdf\n"
                "- Miete/b.pdf\n"
                "- Konto/c.pdf"
            )
        )
    ]


def test_a_failing_download_is_recorded_and_the_run_continues():
    folders = [
        _folder(
            ["Miete"],
            [
                _file("a.pdf", url="/u/a"),
                _file("broken.pdf", url="/u/broken"),
                _file("c.pdf", url="/u/c"),
            ],
        )
    ]
    contents = {"/u/a": b"a", "/u/broken": b"broken", "/u/c": b"c"}
    mietplan = _FakeMietplanClient(
        folders, contents, fail_on={"/u/broken": TimeoutError("read timeout")}
    )
    drive = _FakeGoogleDriveClient()
    handler = Handler(mietplan, drive, _GDRIVE_FOLDER_ID)

    result = handler.handle(Request(max_file_age=None))

    assert handler.report.uploaded == ["Miete/a.pdf", "Miete/c.pdf"]
    assert handler.report.failed == [
        SyncFailure(path="Miete/broken.pdf", error="read timeout")
    ]
    # The failure neither loses the remaining files nor hides them from the message.
    assert [upload.filename for upload in drive.uploads] == [
        "Miete/a.pdf",
        "Miete/c.pdf",
    ]
    assert result == [
        SendMessage(
            message=(
                "Found new mietplan files:\n"
                "- Miete/a.pdf\n"
                "- Miete/c.pdf\n"
                "Failed:\n"
                "- Miete/broken.pdf: read timeout"
            )
        )
    ]


def test_a_run_where_every_file_fails_still_sends_the_failures():
    # The timer's former failure path was an exception reaching the cloud layer.
    # Per-file continuation removed it, so an all-failed night must still produce
    # a Telegram message naming the files that did not make it.
    folders = [
        _folder(
            ["Miete"],
            [_file("a.pdf", url="/u/a"), _file("b.pdf", url="/u/b")],
        )
    ]
    mietplan = _FakeMietplanClient(
        folders,
        {"/u/a": b"a", "/u/b": b"b"},
        fail_on={
            "/u/a": TimeoutError("read timeout"),
            "/u/b": ValueError("not a PDF"),
        },
    )
    handler = Handler(mietplan, _FakeGoogleDriveClient(), _GDRIVE_FOLDER_ID)

    result = handler.handle(Request(max_file_age=None))

    assert handler.report.uploaded == []
    assert handler.report.failed == [
        SyncFailure(path="Miete/a.pdf", error="read timeout"),
        SyncFailure(path="Miete/b.pdf", error="not a PDF"),
    ]
    assert result == [
        SendMessage(
            message=(
                "Found new mietplan files:\n"
                "Failed:\n"
                "- Miete/a.pdf: read timeout\n"
                "- Miete/b.pdf: not a PDF"
            )
        )
    ]


def test_a_dry_run_sends_nothing_even_when_a_lookup_fails():
    class _FailingLookupDrive(_FakeGoogleDriveClient):
        def find_file(self, filename_with_path: str, base_folder_id: str):
            raise RuntimeError("drive unavailable")

    folders = [_folder(["Miete"], [_file("a.pdf", url="/u/a")])]
    handler = Handler(
        _FakeMietplanClient(folders, {"/u/a": b"a"}),
        _FailingLookupDrive(),
        _GDRIVE_FOLDER_ID,
    )

    result = handler.handle(Request(max_file_age=None, dry_run=True))

    assert handler.report.failed == [
        SyncFailure(path="Miete/a.pdf", error="drive unavailable")
    ]
    assert result == []


def test_a_failing_drive_lookup_is_recorded_and_the_run_continues():
    class _FailingLookupDrive(_FakeGoogleDriveClient):
        def find_file(self, filename_with_path: str, base_folder_id: str):
            if filename_with_path == "Miete/a.pdf":
                raise RuntimeError("drive unavailable")
            return super().find_file(filename_with_path, base_folder_id)

    folders = [
        _folder(
            ["Miete"],
            [_file("a.pdf", url="/u/a"), _file("b.pdf", url="/u/b")],
        )
    ]
    handler = Handler(
        _FakeMietplanClient(folders, {"/u/a": b"a", "/u/b": b"b"}),
        _FailingLookupDrive(),
        _GDRIVE_FOLDER_ID,
    )

    handler.handle(Request(max_file_age=None))

    assert handler.report.uploaded == ["Miete/b.pdf"]
    assert handler.report.failed == [
        SyncFailure(path="Miete/a.pdf", error="drive unavailable")
    ]


def test_scanned_folders_counts_every_folder_the_walk_visited():
    folders = [
        _folder(["Archiv"], [], folder_id="folder-empty"),
        _folder(["Archiv", "2019"], [_file("a.pdf", url="/u/a")], folder_id="f-2019"),
        _folder(["Konto"], [], folder_id="folder-konto"),
    ]
    handler, _, _ = _make_handler(folders, {"/u/a": b"a"})

    handler.handle(Request(max_file_age=None, folder="Archiv"))

    assert handler.report.scanned_folders == 3
    assert handler.report.uploaded == ["Archiv/2019/a.pdf"]
