from datetime import datetime
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from sebastian.clients.mietplan.client._walk_from_top_folder import walk_from_top_folder
from sebastian.domain.mietplan import MietplanFile, MietplanFolder

_TOP_FOLDER_ID = "ac4do35ktgfi79j8ids35om8udm"
_GET_FILES = "getFiles"
_GET_FOLDERS = "getFolders"


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeSession:
    def __init__(
        self,
        files: dict[str, list[dict[str, str]]] | None = None,
        folders: dict[str, list[dict[str, Any]]] | None = None,
        failures: dict[tuple[str, str], requests.RequestException] | None = None,
    ) -> None:
        self._files = files or {}
        self._folders = folders or {}
        self._failures = failures or {}
        self.requests: list[tuple[str, str]] = []

    def get(self, url: str, timeout: tuple[int, int]) -> _FakeResponse:
        query = parse_qs(urlparse(url).query)
        message = query["msg"][0]
        folder_id = query["fdFolder"][0]
        self.requests.append((message, folder_id))

        failure = self._failures.get((message, folder_id))
        if failure is not None:
            raise failure

        if message == _GET_FOLDERS:
            return _indexed(self._folders.get(folder_id, []))
        return _indexed(self._files.get(folder_id, []))


def _indexed(rows: list[dict[str, Any]]) -> _FakeResponse:
    return _FakeResponse({str(index): row for index, row in enumerate(rows)})


def _folder_json(
    name: str, folder_id: str, has_subfolders: bool = False
) -> dict[str, Any]:
    return {"filename": name, "fileid": folder_id, "filechildren": has_subfolders}


def _file_json(filecrea: str, filepath: str) -> dict[str, str]:
    return {"filecrea": filecrea, "filepath": filepath}


def _walk(session: _FakeSession) -> list[MietplanFolder]:
    return list(walk_from_top_folder(cast(requests.Session, session), _TOP_FOLDER_ID))


def test_walk_is_depth_first_and_yields_a_parent_before_its_subfolders():
    session = _FakeSession(
        folders={
            _TOP_FOLDER_ID: [
                _folder_json("A", "folder-a", has_subfolders=True),
                _folder_json("B", "folder-b"),
            ],
            "folder-a": [_folder_json("A1", "folder-a1")],
        }
    )

    assert [(folder.id, folder.path) for folder in _walk(session)] == [
        (_TOP_FOLDER_ID, []),
        ("folder-a", ["A"]),
        ("folder-a1", ["A", "A1"]),
        ("folder-b", ["B"]),
    ]


def test_walk_unescapes_file_names_and_takes_the_last_path_segment():
    session = _FakeSession(
        files={
            _TOP_FOLDER_ID: [
                _file_json(
                    "05.03.2024",
                    "/Dateien/M&amp;M/Mieterh&#39;s_&auml;.pdf",
                )
            ]
        }
    )

    assert _walk(session)[0].files == [
        MietplanFile(
            creation_date=datetime(2024, 3, 5),
            name="Mieterh's_ä.pdf",
            url="/Dateien/M&M/Mieterh's_ä.pdf",
        )
    ]


def test_walk_parses_filecrea_as_a_date_in_day_month_year():
    session = _FakeSession(
        files={_TOP_FOLDER_ID: [_file_json("31.12.2025", "/Dateien/a.pdf")]}
    )

    creation_date = _walk(session)[0].files[0].creation_date

    assert creation_date == datetime(2025, 12, 31)
    assert isinstance(creation_date, datetime)


def test_walk_aborts_and_propagates_the_error_when_the_files_request_fails():
    error = requests.Timeout("files request failed")
    session = _FakeSession(
        folders={_TOP_FOLDER_ID: [_folder_json("A", "folder-a")]},
        failures={(_GET_FILES, _TOP_FOLDER_ID): error},
    )

    with pytest.raises(requests.Timeout) as raised:
        next(walk_from_top_folder(session, _TOP_FOLDER_ID))

    assert raised.value is error
    assert session.requests == [(_GET_FILES, _TOP_FOLDER_ID)]


def test_walk_aborts_and_propagates_the_error_when_the_subfolders_request_fails():
    error = requests.ConnectionError("folders request failed")
    session = _FakeSession(
        folders={_TOP_FOLDER_ID: [_folder_json("A", "folder-a")]},
        failures={(_GET_FOLDERS, _TOP_FOLDER_ID): error},
    )

    walker = walk_from_top_folder(session, _TOP_FOLDER_ID)

    # The parent folder is yielded before its subfolders are requested.
    assert next(walker).id == _TOP_FOLDER_ID
    with pytest.raises(requests.ConnectionError) as raised:
        next(walker)

    assert raised.value is error


def test_failure_in_a_subfolder_aborts_the_whole_walk():
    error = requests.HTTPError("folder-a files failed")
    session = _FakeSession(
        folders={
            _TOP_FOLDER_ID: [
                _folder_json("A", "folder-a"),
                _folder_json("B", "folder-b"),
            ]
        },
        failures={(_GET_FILES, "folder-a"): error},
    )

    visited: list[str] = []
    with pytest.raises(requests.HTTPError) as raised:
        for folder in walk_from_top_folder(session, _TOP_FOLDER_ID):
            visited.append(folder.id)

    assert raised.value is error
    assert visited == [_TOP_FOLDER_ID]
    assert (_GET_FILES, "folder-b") not in session.requests
