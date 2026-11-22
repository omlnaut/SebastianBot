"""The Mietplan walk: strict by default (the bot's sync), tolerant on request (seadepot)."""

import pytest
import requests

from sebastian.clients.mietplan.client._walk_from_top_folder import (
    walk_from_top_folder,
    walk_tolerant,
)
from sebastian.domain.mietplan import MietplanWalk
from tests.unit_tests.clients.mietplan._portal import (
    TOP,
    FakeSession,
    empty,
    files,
    folders,
    not_json,
)


def _tree() -> FakeSession:
    return FakeSession(
        {
            ("files", TOP): files(("01.05.2024", "/auctores/root.pdf")),
            ("folders", TOP): folders(("A", "A"), ("B", "B")),
            ("files", "A"): files(("02.06.2023", "/auctores/A/Rechnung &amp; Co.pdf")),
            ("folders", "A"): folders(("A1", "A1")),
            ("files", "A1"): empty(),
            ("folders", "A1"): empty(),
            ("files", "B"): files(("03.07.2022", "/auctores/B/b.pdf")),
            ("folders", "B"): empty(),
        }
    )


def test_the_tolerant_walk_returns_the_tree_depth_first_with_the_parent_first():
    walk = walk_tolerant(_tree(), TOP)

    assert walk.warnings == []
    assert [(folder.id, folder.path) for folder in walk.folders] == [
        (TOP, []),
        ("A", ["A"]),
        ("A1", ["A", "A1"]),
        ("B", ["B"]),
    ]


def test_the_tolerant_walk_maps_unescaped_names_and_parsed_creation_dates():
    walk = walk_tolerant(_tree(), TOP)

    a_files = next(folder for folder in walk.folders if folder.id == "A").files
    assert [(file.name, file.creation_date.isoformat(), file.url) for file in a_files] == [
        ("Rechnung & Co.pdf", "2023-06-02T00:00:00", "/auctores/A/Rechnung & Co.pdf")
    ]


def test_the_tolerant_walk_records_a_warning_for_unreadable_files_and_keeps_walking():
    session = FakeSession(
        {
            ("files", TOP): empty(),
            ("folders", TOP): folders(("A", "A")),
            ("files", "A"): requests.ConnectionError("read timeout"),
            ("folders", "A"): folders(("A1", "A1")),
            ("files", "A1"): files(("04.08.2021", "/auctores/A/A1/deep.pdf")),
            ("folders", "A1"): empty(),
        }
    )

    walk = walk_tolerant(session, TOP)

    assert [(folder.id, folder.path) for folder in walk.folders] == [
        (TOP, []),
        ("A1", ["A", "A1"]),
    ]
    assert [warning.model_dump() for warning in walk.warnings] == [
        {"folder_id": "A", "path": ["A"], "error": "read timeout"}
    ]


def test_the_tolerant_walk_records_a_warning_when_the_subfolders_cannot_be_read():
    session = FakeSession(
        {
            ("files", TOP): files(("01.05.2024", "/auctores/root.pdf")),
            ("folders", TOP): requests.HTTPError("portal boom"),
        }
    )

    walk = walk_tolerant(session, TOP)

    assert [folder.id for folder in walk.folders] == [TOP]
    assert len(walk.folders[0].files) == 1
    assert [(warning.folder_id, warning.path) for warning in walk.warnings] == [
        (TOP, [])
    ]
    assert walk.warnings[0].error == "portal boom"


def test_the_tolerant_walk_reports_a_non_json_answer_as_a_warning_not_a_crash():
    """An expired session answers getFolders with HTML, not the file tree."""
    session = FakeSession(
        {
            ("files", TOP): empty(),
            ("folders", TOP): not_json(),
        }
    )

    walk = walk_tolerant(session, TOP)

    assert [(warning.folder_id, warning.error) for warning in walk.warnings] == [
        (TOP, "Expecting value: line 1 column 1 (char 0)")
    ]


def test_the_tolerant_walk_returns_a_domain_walk_object():
    assert isinstance(walk_tolerant(_tree(), TOP), MietplanWalk)


def test_the_strict_walk_still_aborts_on_the_first_failing_folder():
    session = FakeSession(
        {
            ("files", TOP): empty(),
            ("folders", TOP): folders(("A", "A")),
            ("files", "A"): requests.ConnectionError("read timeout"),
        }
    )
    portal = walk_from_top_folder(session, TOP)

    assert next(portal).id == TOP
    with pytest.raises(requests.ConnectionError, match="read timeout"):
        next(portal)


def test_the_strict_walk_yields_the_same_tree_as_the_tolerant_one():
    strict = list(walk_from_top_folder(_tree(), TOP))

    assert strict == walk_tolerant(_tree(), TOP).folders
