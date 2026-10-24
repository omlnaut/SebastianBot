import json
from pathlib import Path

import pytest

from sebastian.clients.google.gmail.attachments import (
    sanitize_filename,
    write_attachments,
)
from sebastian.clients.google.gmail.errors import AttachmentWriteError
from sebastian.clients.google.gmail.parsing import parse_payload
from sebastian.domain.gmail import ParsedAttachment

FIXTURES = Path(__file__).parent / "fixtures" / "gmail"


def _parsed(name: str):
    return parse_payload(json.loads((FIXTURES / name).read_text()))


def _attachment(filename: str, attachment_id: str = "att-1") -> ParsedAttachment:
    return ParsedAttachment(
        filename=filename,
        mime_type="application/pdf",
        size=6,
        attachment_id=attachment_id,
    )


def _fetch(attachment_id: str) -> bytes:
    return f"data-for-{attachment_id}".encode()


def test_nested_attachments_from_a_mail_are_written(tmp_path):
    parsed = _parsed("nested_attachment.json")

    written = write_attachments(parsed.attachments, tmp_path, False, _fetch)

    assert [(Path(item.path).name, item.size) for item in written] == [
        ("Rechnung.pdf", len(_fetch("att-1")))
    ]
    assert (tmp_path / "Rechnung.pdf").read_bytes() == _fetch("att-1")


def test_attachment_content_is_fetched_in_the_same_call(tmp_path):
    fetched: list[str] = []

    def fetch(attachment_id: str) -> bytes:
        fetched.append(attachment_id)
        return b"payload"

    written = write_attachments([_attachment("a.pdf", "att-a")], tmp_path, False, fetch)

    assert fetched == ["att-a"]
    assert written[0].size == len(b"payload")


def test_inline_attachment_content_is_not_fetched(tmp_path):
    attachment = ParsedAttachment(
        filename="inline.txt",
        mime_type="text/plain",
        size=6,
        attachment_id=None,
        inline_data=b"inline",
    )
    fetched: list[str] = []

    written = write_attachments([attachment], tmp_path, False, fetched.append)

    assert fetched == []
    assert (tmp_path / "inline.txt").read_bytes() == b"inline"
    assert written[0].size == len(b"inline")


def test_traversal_filename_cannot_escape_the_output_directory(tmp_path):
    out = tmp_path / "out"
    out.mkdir()

    written = write_attachments(
        [_attachment("../../../etc/passwd")], out, False, _fetch
    )

    target = Path(written[0].path)
    assert target.parent == out
    assert target == out / "_.._.._etc_passwd"
    assert target.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["out"]


def test_windows_style_traversal_is_neutralized_within_the_output_directory(
    tmp_path,
):
    written = write_attachments(
        [_attachment("..\\..\\evil.sh")], tmp_path, False, _fetch
    )

    assert Path(written[0].path) == tmp_path / "_.._evil.sh"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["_.._evil.sh"]


def test_dot_only_filenames_get_a_safe_default(tmp_path):
    written = write_attachments([_attachment("..")], tmp_path, False, _fetch)

    assert Path(written[0].path) == tmp_path / "attachment"


def test_sanitize_filename_replaces_separators_instead_of_truncating():
    assert (
        sanitize_filename("121901_Infoblatt Antrag/NachweisService.pdf")
        == "121901_Infoblatt Antrag_NachweisService.pdf"
    )
    assert (
        sanitize_filename("Postbank\\Rechnung.pdf") == "Postbank_Rechnung.pdf"
    )


def test_sanitize_filename_strips_control_characters_and_leading_dots():
    assert sanitize_filename("../../x\n.pdf") == "_.._x.pdf"
    assert sanitize_filename(".hidden") == "hidden"


def test_existing_files_are_not_overwritten_without_force(tmp_path):
    (tmp_path / "Rechnung.pdf").write_bytes(b"keep me")

    with pytest.raises(AttachmentWriteError) as error:
        write_attachments([_attachment("Rechnung.pdf")], tmp_path, False, _fetch)

    assert "refusing to overwrite" in str(error.value)
    assert (tmp_path / "Rechnung.pdf").read_bytes() == b"keep me"


def test_existing_files_are_overwritten_with_force(tmp_path):
    (tmp_path / "Rechnung.pdf").write_bytes(b"old")

    write_attachments([_attachment("Rechnung.pdf")], tmp_path, True, _fetch)

    assert (tmp_path / "Rechnung.pdf").read_bytes() == _fetch("att-1")


def test_duplicate_filenames_within_one_mail_get_distinct_paths(tmp_path):
    attachments = [
        _attachment("report.pdf", "att-1"),
        _attachment("report.pdf", "att-2"),
        _attachment("dir/report.pdf", "att-3"),
    ]

    written = write_attachments(attachments, tmp_path, False, _fetch)

    assert [Path(item.path).name for item in written] == [
        "report.pdf",
        "report-2.pdf",
        "dir_report.pdf",
    ]
    assert (tmp_path / "report-2.pdf").read_bytes() == _fetch("att-2")


def test_a_missing_output_directory_is_created(tmp_path):
    missing = tmp_path / "fresh" / "nested"

    written = write_attachments([_attachment("a.pdf")], missing, False, _fetch)

    assert Path(written[0].path) == missing / "a.pdf"
    assert (missing / "a.pdf").read_bytes() == _fetch("att-1")


def test_an_output_path_that_is_a_file_is_an_io_error(tmp_path):
    blocker = tmp_path / "not-a-directory"
    blocker.write_bytes(b"x")

    with pytest.raises(AttachmentWriteError) as error:
        write_attachments([_attachment("a.pdf")], blocker, False, _fetch)

    assert "could not create output directory" in str(error.value)


def test_an_attachment_without_content_or_id_is_an_io_error(tmp_path):
    attachment = ParsedAttachment(
        filename="broken.pdf", mime_type="application/pdf", size=0
    )

    with pytest.raises(AttachmentWriteError):
        write_attachments([attachment], tmp_path, False, _fetch)
