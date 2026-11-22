"""The `seadepot` CLI, exercised through `run(argv, service)` with a fake service.

The service seam is the client's tolerant walk: filters, the result limit and the
JSON envelope all live in the CLI, so these tests pin behaviour the agent sees.
No network, no credentials, no portal.
"""

import json
from datetime import datetime
from typing import Any, Sequence

import pytest
import requests

from cli.mietplan import build_service_from_env, main, run
from sebastian.clients.mietplan.download import download_to_dir
from sebastian.clients.mietplan.env_credentials import ENV_VAR
from sebastian.clients.mietplan.errors import MietplanAuthError
from sebastian.domain.mietplan import (
    MietplanFile,
    MietplanFolder,
    MietplanWalk,
    MietplanWalkWarning,
)


class _FakeService:
    """Returns a fixed walk and records that it was asked exactly once."""

    def __init__(self, walk: MietplanWalk | None = None):
        self._walk = walk if walk is not None else MietplanWalk(folders=[], warnings=[])
        self.walks = 0

    def walk_tolerant(self) -> MietplanWalk:
        self.walks += 1
        return self._walk


class _WalkWithoutTolerance:
    """A service that only has the strict walk: the CLI must never use it."""

    def walk_from_top_folder(self):
        raise AssertionError("search must not use the strict walk")

    def walk_tolerant(self) -> MietplanWalk:
        return MietplanWalk(folders=[], warnings=[])


def _file(
    name: str,
    created: str = "2024-05-01",
    url: str = "/auctores/doc/file.pdf",
) -> MietplanFile:
    return MietplanFile(
        creation_date=datetime.strptime(created, "%Y-%m-%d"),
        name=name,
        url=url,
    )


def _folder(
    folder_id: str, path: list[str], files: Sequence[MietplanFile] = ()
) -> MietplanFolder:
    return MietplanFolder(id=folder_id, path=path, files=list(files))


def _walk(
    *folders: MietplanFolder, warnings: Sequence[MietplanWalkWarning] = ()
) -> MietplanWalk:
    return MietplanWalk(folders=list(folders), warnings=list(warnings))


def _payload(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    captured = capsys.readouterr()
    assert captured.err == ""
    payload: dict[str, Any] = json.loads(captured.out)
    return payload


def _error(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    captured = capsys.readouterr()
    assert captured.out == ""
    payload: dict[str, Any] = json.loads(captured.err)
    return payload


def test_search_emits_one_json_object_with_the_documented_envelope(
    capsys: pytest.CaptureFixture[str],
):
    service = _FakeService(
        _walk(
            _folder(
                "f1",
                ["Nebenkostenabrechnung"],
                [_file("2024.pdf", created="2024-05-01", url="/auctores/a/2024.pdf")],
            )
        )
    )

    code = run(["search"], service)

    assert code == 0
    assert _payload(capsys) == {
        "command": "search",
        "filters": {
            "substring": None,
            "folder": None,
            "after": None,
            "before": None,
            "limit": 50,
        },
        "count": 1,
        "scannedFolders": 1,
        "truncated": False,
        "files": [
            {
                "path": "Nebenkostenabrechnung/2024.pdf",
                "folderId": "f1",
                "name": "2024.pdf",
                "creationDate": "2024-05-01",
                "url": "/auctores/a/2024.pdf",
            }
        ],
        "warnings": [],
    }


def test_search_echoes_every_filter_it_was_given(capsys: pytest.CaptureFixture[str]):
    code = run(
        [
            "search",
            "nebenkosten",
            "--folder",
            "Archiv",
            "--after",
            "2024-01-01",
            "--before",
            "2024-12-31",
            "--limit",
            "7",
        ],
        _FakeService(),
    )

    assert code == 0
    assert _payload(capsys)["filters"] == {
        "substring": "nebenkosten",
        "folder": "Archiv",
        "after": "2024-01-01",
        "before": "2024-12-31",
        "limit": 7,
    }


def test_search_never_uses_the_strict_walk(capsys: pytest.CaptureFixture[str]):
    code = run(["search"], _WalkWithoutTolerance())

    assert code == 0
    assert _payload(capsys)["count"] == 0


def test_an_empty_tree_is_an_empty_result_not_an_error(
    capsys: pytest.CaptureFixture[str],
):
    code = run(["search"], _FakeService(_walk()))

    assert code == 0
    payload = _payload(capsys)
    assert payload["count"] == 0
    assert payload["scannedFolders"] == 0
    assert payload["files"] == []


def _names(payload: dict[str, Any]) -> list[str]:
    return [entry["name"] for entry in payload["files"]]


def _tree() -> MietplanWalk:
    return _walk(
        _folder("f1", ["Nebenkostenabrechnung"], [_file("2024.pdf")]),
        _folder("f2", ["Mietvertrag"], [_file("Vertrag 2023.pdf")]),
        _folder("f3", [], [_file("Nebenkosten-2022.pdf")]),
        _folder(
            "f4",
            ["Archiv", "2019"],
            [_file("alt.pdf", created="2019-03-01")],
        ),
        _folder(
            "f5",
            ["Archiv", "2020"],
            [_file("neu.pdf", created="2020-03-01")],
        ),
    )


def test_the_substring_is_matched_case_insensitively_against_the_path(
    capsys: pytest.CaptureFixture[str],
):
    run(["search", "NEBENKOSTEN"], _FakeService(_tree()))

    assert _names(_payload(capsys)) == ["2024.pdf", "Nebenkosten-2022.pdf"]


def test_the_substring_also_matches_the_folder_part_of_the_path(
    capsys: pytest.CaptureFixture[str],
):
    run(["search", "mietvertrag"], _FakeService(_tree()))

    assert _names(_payload(capsys)) == ["Vertrag 2023.pdf"]


def test_a_substring_that_matches_nothing_is_an_empty_result(
    capsys: pytest.CaptureFixture[str],
):
    run(["search", "dachsanierung"], _FakeService(_tree()))

    payload = _payload(capsys)
    assert payload["files"] == []
    assert payload["count"] == 0
    assert payload["truncated"] is False


def test_the_folder_filter_is_a_path_prefix_not_a_substring(
    capsys: pytest.CaptureFixture[str],
):
    service = _FakeService(_tree())

    run(["search", "--folder", "Archiv"], service)
    assert _names(_payload(capsys)) == ["alt.pdf", "neu.pdf"]

    run(["search", "--folder", "Archiv/2019"], service)
    assert _names(_payload(capsys)) == ["alt.pdf"]

    run(["search", "--folder", "2019"], service)
    assert _names(_payload(capsys)) == []


def test_the_folder_filter_ignores_a_leading_slash(
    capsys: pytest.CaptureFixture[str],
):
    run(["search", "--folder", "/Archiv/2020"], _FakeService(_tree()))

    assert _names(_payload(capsys)) == ["neu.pdf"]


def _dated() -> MietplanWalk:
    return _walk(
        _folder(
            "f",
            [],
            [
                _file("a.pdf", created="2023-12-31"),
                _file("b.pdf", created="2024-01-01"),
                _file("c.pdf", created="2024-06-15"),
                _file("d.pdf", created="2024-12-31"),
                _file("e.pdf", created="2025-01-01"),
            ],
        )
    )


def test_after_and_before_bound_the_creation_date_inclusively(
    capsys: pytest.CaptureFixture[str],
):
    run(
        ["search", "--after", "2024-01-01", "--before", "2024-12-31"],
        _FakeService(_dated()),
    )

    assert _names(_payload(capsys)) == ["b.pdf", "c.pdf", "d.pdf"]


def test_after_is_an_inclusive_lower_bound(
    capsys: pytest.CaptureFixture[str],
):
    run(["search", "--after", "2024-01-01"], _FakeService(_dated()))

    assert _names(_payload(capsys)) == ["b.pdf", "c.pdf", "d.pdf", "e.pdf"]


def test_before_is_an_inclusive_upper_bound(
    capsys: pytest.CaptureFixture[str],
):
    run(["search", "--before", "2024-12-31"], _FakeService(_dated()))

    assert _names(_payload(capsys)) == ["a.pdf", "b.pdf", "c.pdf", "d.pdf"]


def _many(count: int) -> MietplanWalk:
    return _walk(_folder("f", ["Archiv"], [_file(f"doc-{i}.pdf") for i in range(count)]))


def test_the_default_limit_prints_fifty_of_fifty_one_files_and_flags_truncation(
    capsys: pytest.CaptureFixture[str],
):
    run(["search"], _FakeService(_many(51)))

    payload = _payload(capsys)
    assert payload["count"] == 50
    assert len(payload["files"]) == 50
    assert payload["truncated"] is True
    assert _names(payload)[0] == "doc-0.pdf"
    assert _names(payload)[-1] == "doc-49.pdf"


def test_a_limit_truncates_the_result_list_in_walk_order(
    capsys: pytest.CaptureFixture[str],
):
    run(["search", "--limit", "2"], _FakeService(_many(3)))

    payload = _payload(capsys)
    assert _names(payload) == ["doc-0.pdf", "doc-1.pdf"]
    assert payload["count"] == 2
    assert payload["truncated"] is True


def test_exactly_the_limit_is_not_truncated(capsys: pytest.CaptureFixture[str]):
    run(["search", "--limit", "3"], _FakeService(_many(3)))

    payload = _payload(capsys)
    assert payload["count"] == 3
    assert payload["truncated"] is False


def test_a_limit_above_the_hard_cap_is_clamped_to_five_hundred(
    capsys: pytest.CaptureFixture[str],
):
    run(["search", "--limit", "900"], _FakeService(_many(501)))

    payload = _payload(capsys)
    assert payload["filters"]["limit"] == 500
    assert payload["count"] == 500
    assert payload["truncated"] is True


def test_the_limit_truncates_the_result_list_but_the_walk_still_runs_to_the_end(
    capsys: pytest.CaptureFixture[str],
):
    service = _FakeService(
        _walk(
            _folder("f1", ["a"], [_file("one.pdf")]),
            _folder("f2", ["b"], [_file("two.pdf")]),
            _folder("f3", ["c"], [_file("three.pdf")]),
        )
    )

    run(["search", "--limit", "1"], service)

    payload = _payload(capsys)
    assert payload["count"] == 1
    assert payload["scannedFolders"] == 3
    assert payload["truncated"] is True
    assert service.walks == 1


def test_unreadable_folders_are_warnings_and_still_exit_zero(
    capsys: pytest.CaptureFixture[str],
):
    service = _FakeService(
        _walk(
            _folder("f1", ["Archiv"], [_file("2024.pdf")]),
            warnings=[
                MietplanWalkWarning(
                    folder_id="f9", path=["Archiv", "2019"], error="read timeout"
                )
            ],
        )
    )

    code = run(["search"], service)

    assert code == 0
    payload = _payload(capsys)
    assert payload["warnings"] == [
        {"folderId": "f9", "path": "Archiv/2019", "error": "read timeout"}
    ]
    assert payload["count"] == 1
    assert payload["scannedFolders"] == 1


def test_a_warning_does_not_become_a_filter_or_a_file(
    capsys: pytest.CaptureFixture[str],
):
    service = _FakeService(
        _walk(
            warnings=[
                MietplanWalkWarning(
                    folder_id="f9", path=["Archiv"], error="read timeout"
                )
            ],
        )
    )

    code = run(["search", "archiv"], service)

    assert code == 0
    payload = _payload(capsys)
    assert payload["files"] == []
    assert payload["warnings"][0]["folderId"] == "f9"


class _RaisingService:
    def __init__(self, error: Exception):
        self._error = error

    def walk_tolerant(self) -> MietplanWalk:
        raise self._error


def test_a_bad_date_is_a_usage_error(capsys: pytest.CaptureFixture[str]):
    code = run(["search", "--after", "2024-1-1"], _FakeService())

    assert code == 2
    error = _error(capsys)
    assert error["command"] == "search"
    assert error["error"]["kind"] == "usage"
    assert "--after" in error["error"]["message"]
    assert "YYYY-MM-DD" in error["error"]["message"]


def test_a_limit_below_one_is_a_usage_error(capsys: pytest.CaptureFixture[str]):
    code = run(["search", "--limit", "0"], _FakeService())

    assert code == 2
    error = _error(capsys)
    assert error["error"]["kind"] == "usage"
    assert "--limit" in error["error"]["message"]


def test_an_unknown_flag_is_a_usage_error(capsys: pytest.CaptureFixture[str]):
    code = run(["search", "--nope"], _FakeService())

    assert code == 2
    assert _error(capsys) == {
        "command": "search",
        "error": {"kind": "usage", "message": "unrecognized arguments: --nope"},
    }


def test_a_second_positional_argument_is_a_usage_error(
    capsys: pytest.CaptureFixture[str],
):
    code = run(["search", "nebenkosten", "vertrag"], _FakeService())

    assert code == 2
    assert _error(capsys)["error"]["kind"] == "usage"


def test_a_missing_command_is_a_usage_error(capsys: pytest.CaptureFixture[str]):
    code = run([], _FakeService())

    assert code == 2
    error = _error(capsys)
    assert error["command"] is None
    assert error["error"]["kind"] == "usage"


def test_a_rejected_session_is_an_auth_error(capsys: pytest.CaptureFixture[str]):
    service = _RaisingService(MietplanAuthError("login was rejected: HTTP 403", 403))

    code = run(["search"], service)

    assert code == 1
    assert _error(capsys) == {
        "command": "search",
        "error": {"kind": "auth", "message": "login was rejected: HTTP 403"},
    }


def test_a_portal_failure_is_an_api_error(capsys: pytest.CaptureFixture[str]):
    code = run(["search"], _RaisingService(requests.HTTPError("portal boom")))

    assert code == 1
    assert _error(capsys) == {
        "command": "search",
        "error": {"kind": "api", "message": "portal boom"},
    }


def test_a_filesystem_failure_is_an_io_error(capsys: pytest.CaptureFixture[str]):
    code = run(["search"], _RaisingService(OSError("no space left on device")))

    assert code == 1
    assert _error(capsys) == {
        "command": "search",
        "error": {"kind": "io", "message": "no space left on device"},
    }


def test_success_prints_exactly_one_json_object_and_nothing_else(
    capsys: pytest.CaptureFixture[str],
):
    run(["search"], _FakeService(_tree()))

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    assert json.loads(captured.out)["command"] == "search"


def test_usage_errors_are_reported_before_the_service_is_built(
    capsys: pytest.CaptureFixture[str],
):
    def factory():
        raise AssertionError("an invalid invocation must not build the service")

    code = main(["search", "--limit", "0"], service_factory=factory)

    assert code == 2
    assert _error(capsys)["error"]["kind"] == "usage"


def test_a_rejected_login_at_construction_is_an_auth_error(
    capsys: pytest.CaptureFixture[str],
):
    def factory():
        raise MietplanAuthError("login was rejected: HTTP 403", 403)

    code = main(["search"], service_factory=factory)

    assert code == 1
    assert _error(capsys)["error"]["kind"] == "auth"


def test_a_portal_failure_at_construction_is_an_api_error(
    capsys: pytest.CaptureFixture[str],
):
    def factory():
        raise requests.ConnectionError("portal unreachable")

    code = main(["search"], service_factory=factory)

    assert code == 1
    assert _error(capsys)["error"]["kind"] == "api"


def test_missing_credentials_is_an_auth_error_naming_the_variable(
    capsys: pytest.CaptureFixture[str],
):
    code = main(["search"], service_factory=lambda: build_service_from_env({}))

    assert code == 1
    error = _error(capsys)
    assert error["error"]["kind"] == "auth"
    assert ENV_VAR in error["error"]["message"]


def test_invalid_credentials_json_is_an_auth_error(
    capsys: pytest.CaptureFixture[str],
):
    code = main(
        ["search"],
        service_factory=lambda: build_service_from_env({ENV_VAR: "{not json"}),
    )

    assert code == 1
    error = _error(capsys)
    assert error["error"]["kind"] == "auth"
    assert ENV_VAR in error["error"]["message"]


class _DownloadService:
    """A fake portal: a fixed walk plus fixed bytes fetched through the real writer.

    Resolution, sanitization and the overwrite guard are production code (the same
    function `MietplanClient.download` calls); only the portal is faked.
    """

    def __init__(
        self,
        walk: MietplanWalk | None = None,
        content: bytes = b"%PDF-1.4 fake document",
        error: Exception | None = None,
    ):
        self._walk = walk if walk is not None else MietplanWalk(folders=[], warnings=[])
        self._content = content
        self._error = error
        self.downloads: list[str] = []

    def walk_tolerant(self) -> MietplanWalk:
        return self._walk

    def download_file(self, download_path: str) -> bytes:
        self.downloads.append(download_path)
        return self._content

    def download(self, path: str, out_dir: str, force: bool):
        if self._error is not None:
            raise self._error
        return download_to_dir(path, out_dir, force, self._walk, self.download_file)


def _download_tree() -> MietplanWalk:
    return _walk(
        _folder(
            "f1",
            ["Nebenkostenabrechnung", "2024"],
            [
                _file(
                    "März & Co (final).pdf",
                    url="/auctores/Nebenkostenabrechnung/2024/März & Co (final).pdf",
                )
            ],
        )
    )


def test_download_mirrors_the_folder_path_under_out_and_reports_the_file(
    capsys: pytest.CaptureFixture[str], tmp_path
):
    portal_path = "Nebenkostenabrechnung/2024/März & Co (final).pdf"
    service = _DownloadService(_download_tree(), content=b"%PDF-1.4 real bytes")

    code = run(["download", portal_path, "--out", str(tmp_path / "out")], service)

    assert code == 0
    target = tmp_path / "out" / "Nebenkostenabrechnung" / "2024" / "März & Co (final).pdf"
    assert target.read_bytes() == b"%PDF-1.4 real bytes"
    assert service.downloads == [
        "/auctores/Nebenkostenabrechnung/2024/März & Co (final).pdf"
    ]
    payload = _payload(capsys)
    assert payload == {
        "command": "download",
        "path": portal_path,
        "file": {"path": str(target.resolve()), "bytes": len(b"%PDF-1.4 real bytes")},
    }
