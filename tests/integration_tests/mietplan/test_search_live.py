"""`seadepot search` against the live webdepot.

Every invocation is one full walk of the tree (V5: minutes on the real tree), so
the whole-tree payload is built once per session and reused. Skipped cleanly
without `SEAMIETPLAN_CREDENTIALS`.
"""

import io
import json
from contextlib import redirect_stdout
from typing import Any, Sequence

import pytest

from cli.mietplan import run
from sebastian.clients.mietplan.client.client import MietplanClient

MAX_FILES = "500"


def _search(client: MietplanClient, argv: Sequence[str]) -> dict[str, Any]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = run(argv, client)
    assert code == 0, f"search failed with exit code {code}"
    payload: dict[str, Any] = json.loads(buffer.getvalue())
    return payload


@pytest.fixture(scope="session")
def whole_tree(mietplan_client: MietplanClient) -> dict[str, Any]:
    return _search(mietplan_client, ["search", "--limit", MAX_FILES])


def test_search_walks_the_tree_and_reports_its_extent(whole_tree: dict[str, Any]):
    assert whole_tree["command"] == "search"
    assert whole_tree["scannedFolders"] > 0
    assert whole_tree["count"] > 0
    assert len(whole_tree["files"]) == whole_tree["count"]
    assert whole_tree["filters"]["limit"] == int(MAX_FILES)


def test_every_file_carries_the_documented_shape(whole_tree: dict[str, Any]):
    for entry in whole_tree["files"]:
        assert set(entry) == {"path", "folderId", "name", "creationDate", "url"}
        assert entry["path"].endswith(entry["name"])
        assert entry["url"].startswith("/")
        assert len(entry["creationDate"]) == 10
        assert entry["creationDate"][4] == "-"
        assert entry["creationDate"][7] == "-"


def test_the_substring_filter_narrows_the_result(
    mietplan_client: MietplanClient, whole_tree: dict[str, Any]
):
    sample = whole_tree["files"][0]

    payload = _search(mietplan_client, ["search", sample["name"], "--limit", MAX_FILES])

    assert payload["count"] > 0
    assert sample["path"] in {entry["path"] for entry in payload["files"]}
    assert all(
        sample["name"].lower() in entry["path"].lower() for entry in payload["files"]
    )


def test_the_folder_filter_narrows_the_result_to_that_subtree(
    mietplan_client: MietplanClient, whole_tree: dict[str, Any]
):
    nested = next(
        (entry for entry in whole_tree["files"] if "/" in entry["path"]), None
    )
    if nested is None:
        pytest.skip("the webdepot has no file inside a subfolder right now")
    prefix = nested["path"].rsplit("/", 1)[0]

    payload = _search(mietplan_client, ["search", "--folder", prefix, "--limit", MAX_FILES])

    assert payload["count"] > 0
    assert all(entry["path"].startswith(f"{prefix}/") for entry in payload["files"])


def test_the_date_range_is_inclusive_of_both_boundaries(
    mietplan_client: MietplanClient, whole_tree: dict[str, Any]
):
    dates = sorted(entry["creationDate"] for entry in whole_tree["files"])
    if len(dates) < 2:
        pytest.skip("the webdepot does not carry two distinct creation dates")
    after, before = dates[0], dates[-1]

    payload = _search(
        mietplan_client,
        ["search", "--after", after, "--before", before, "--limit", MAX_FILES],
    )

    assert all(after <= entry["creationDate"] <= before for entry in payload["files"])
    assert dates[0] in {entry["creationDate"] for entry in payload["files"]}


def test_the_limit_truncates_the_printed_list_and_flags_it(
    mietplan_client: MietplanClient, whole_tree: dict[str, Any]
):
    payload = _search(mietplan_client, ["search", "--limit", "1"])

    assert payload["count"] <= 1
    assert payload["scannedFolders"] == whole_tree["scannedFolders"]
    assert payload["truncated"] is (whole_tree["count"] > 1)
