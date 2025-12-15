"""
Architecture tests to enforce import boundaries and separation of concerns.

Uses pytest-archon to validate import constraints in a declarative way.
"""
from pytest_archon import archrule


def test_sebastian_should_not_import_cloud():
    """Ensure no file in sebastian imports anything from cloud (infrastructure layer)."""
    (
        archrule("sebastian should not import cloud")
        .match("sebastian.*")
        .should_not_import("cloud.*")
        .check("sebastian")
    )


def test_protocols_should_only_import_from_protocols():
    """Ensure protocol files only import from within protocols module or standard/external libraries."""
    (
        archrule("protocols should only import from protocols")
        .match("sebastian.protocols.*")
        .should_not_import("sebastian.*")
        .may_import("sebastian.protocols.*")
        .check("sebastian")
    )

