"""The seamail CLI is add-only: it may create a draft and nothing else.

Sending is the human's click, not a missing feature. This test is the guarantee:
if a send call ever appears in the shipped package, the suite fails before the
agent could be wired up to it.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOTS = ("cli", "sebastian")

SEND_CALL = re.compile(r"\.send\s*\(")


def _package_sources() -> list[Path]:
    return [
        path
        for root in PACKAGE_ROOTS
        for path in sorted((REPO_ROOT / root).rglob("*.py"))
    ]


def test_the_guard_finds_the_package_sources():
    assert len(_package_sources()) > 10


def test_no_module_calls_a_send_api():
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in _package_sources()
        if SEND_CALL.search(path.read_text(encoding="utf-8"))
    ]

    assert (
        offenders == []
    ), "seamail must never send mail; remove the send call from: " + ", ".join(
        offenders
    )


def test_the_only_gmail_write_is_draft_creation():
    writes = [
        str(path.relative_to(REPO_ROOT))
        for path in _package_sources()
        if ".drafts()" in path.read_text(encoding="utf-8")
        or ".messages()" in path.read_text(encoding="utf-8")
    ]

    assert writes == ["sebastian/clients/google/gmail/client/service_wrapper.py"]
