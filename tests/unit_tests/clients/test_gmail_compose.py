import base64
from email import message_from_bytes, policy
from email.message import EmailMessage

import pytest

from sebastian.clients.google.gmail import compose
from sebastian.clients.google.gmail.compose import (
    compose_draft,
    derive_reply_target,
    parse_recipients,
    parse_renames,
    resolve_attachments,
)
from sebastian.clients.google.gmail.errors import DraftInputError, DraftIoError
from sebastian.domain.gmail import (
    DraftRequest,
    ReplyContext,
)


def _request(
    body: str = "Hallo,\n\nalles gut.\n",
    attachments=(),
    **overrides,
) -> DraftRequest:
    fields = {
        "to": ["Alice <alice@example.com>"],
        "cc": [],
        "bcc": [],
        "subject": "Kurzfrage",
        "body": body,
        "attachments": list(attachments),
    }
    fields.update(overrides)
    return DraftRequest(**fields)


def _parsed(composed) -> EmailMessage:
    return message_from_bytes(composed.raw, policy=policy.default)


def test_compose_sets_recipients_subject_and_plain_text_body():
    composed = compose_draft(_request(cc=["bob@example.com"]))

    message = _parsed(composed)
    assert message["To"] == "Alice <alice@example.com>"
    assert message["Cc"] == "bob@example.com"
    assert message["Subject"] == "Kurzfrage"
    assert message.get_content_type() == "text/plain"
    assert message.get_content() == "Hallo,\n\nalles gut.\n"


def test_compose_never_sets_from_because_gmail_fills_it():
    composed = compose_draft(_request())

    assert _parsed(composed)["From"] is None


def test_compose_omits_an_empty_subject_header():
    composed = compose_draft(_request(subject=""))

    assert _parsed(composed)["Subject"] is None


def test_umlaut_subject_is_rfc2047_encoded_and_reads_back_intact():
    composed = compose_draft(_request(subject="Grüße aus Dresden äöü"))

    assert b"=?utf-8?" in composed.raw.lower()
    assert _parsed(composed)["Subject"] == "Grüße aus Dresden äöü"


def test_non_ascii_attachment_filename_is_rfc2231_encoded(tmp_path):
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"%PDF-1.7 fake")
    attachments = resolve_attachments(
        [str(path)], {"scan.pdf": "Rechnung Oktober äöü.pdf"}
    )

    composed = compose_draft(_request(attachments=attachments))

    assert b"filename*=" in composed.raw
    parts = [part for part in _parsed(composed).iter_attachments()]
    assert [part.get_filename() for part in parts] == ["Rechnung Oktober äöü.pdf"]


def test_attachment_bytes_round_trip_through_the_mime_message(tmp_path):
    path = tmp_path / "note.bin"
    payload = bytes(range(256)) * 4
    path.write_bytes(payload)
    attachments = resolve_attachments([str(path)], {})

    composed = compose_draft(_request(attachments=attachments))

    part = next(iter(_parsed(composed).iter_attachments()))
    assert part.get_content_type() == "application/octet-stream"
    assert part.get_payload(decode=True) == payload


def test_attachment_mime_type_is_guessed_from_the_visible_filename(tmp_path):
    path = tmp_path / "upload.txt"
    path.write_bytes(b"data")
    attachments = resolve_attachments([str(path)], {"upload.txt": "Rechnung.pdf"})

    composed = compose_draft(_request(attachments=attachments))

    part = next(iter(_parsed(composed).iter_attachments()))
    assert part.get_content_type() == "application/pdf"


def test_encoded_size_counts_the_base64_message():
    composed = compose_draft(_request())

    assert composed.encoded == base64.urlsafe_b64encode(composed.raw).decode("ascii")
    assert composed.encoded_bytes == len(composed.encoded)


def test_oversized_message_is_a_usage_error_naming_the_files(tmp_path, monkeypatch):
    path = tmp_path / "big.pdf"
    path.write_bytes(b"x" * 4096)
    attachments = resolve_attachments([str(path)], {"big.pdf": "Gross.pdf"})
    monkeypatch.setattr(compose, "MAX_ENCODED_BYTES", 2048)

    with pytest.raises(DraftInputError) as error:
        compose_draft(_request(attachments=attachments))

    assert "Gross.pdf (4096 bytes)" in str(error.value)
    assert "2048" in str(error.value)


def test_a_draft_without_recipients_is_a_usage_error():
    with pytest.raises(DraftInputError, match="recipient"):
        compose_draft(_request(to=[]))


def test_a_subject_with_a_line_break_is_rejected():
    with pytest.raises(DraftInputError, match="line break"):
        compose_draft(_request(subject="hello\nBcc: victim@example.com"))


def test_a_recipient_with_a_line_break_is_rejected():
    with pytest.raises(DraftInputError, match="line break"):
        parse_recipients(["alice@example.com\r\nBcc: victim@example.com"])


def test_parse_recipients_accepts_comma_lists_and_repeats_and_dedupes():
    recipients = parse_recipients(
        ["Alice <alice@example.com>, bob@example.com", "ALICE@example.com"]
    )

    assert recipients == ["Alice <alice@example.com>", "bob@example.com"]


def test_parse_recipients_rejects_an_unparseable_address():
    with pytest.raises(DraftInputError, match="not a usable email address"):
        parse_recipients(["not an address"])


def test_parse_renames_splits_basename_and_new_name():
    assert parse_renames(["scan.pdf=Rechnung.pdf"]) == {"scan.pdf": "Rechnung.pdf"}


def test_parse_renames_rejects_a_missing_equals_sign():
    with pytest.raises(DraftInputError, match="<basename>=<newname>"):
        parse_renames(["scan.pdf"])


def test_parse_renames_rejects_path_separators_in_the_new_name():
    with pytest.raises(DraftInputError, match="path separators"):
        parse_renames(["scan.pdf=../evil.pdf"])


def test_parse_renames_rejects_an_empty_new_name():
    with pytest.raises(DraftInputError, match="must not be empty"):
        parse_renames(["scan.pdf="])


def test_resolve_attachments_rejects_a_rename_for_an_absent_attachment(tmp_path):
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"pdf")

    with pytest.raises(DraftInputError, match="refers to no attachment: other.pdf"):
        resolve_attachments([str(path)], {"other.pdf": "x.pdf"})


def test_resolve_attachments_rejects_two_attachments_with_one_name(tmp_path):
    first = tmp_path / "a" / "scan.pdf"
    second = tmp_path / "b" / "scan.pdf"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_bytes(b"one")
    second.write_bytes(b"two")

    with pytest.raises(DraftInputError, match="both be named 'scan.pdf'"):
        resolve_attachments([str(first), str(second)], {})


def test_resolve_attachments_rejects_renaming_two_files_onto_one_name(tmp_path):
    first = tmp_path / "a" / "scan.pdf"
    second = tmp_path / "b" / "photo.jpg"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_bytes(b"one")
    second.write_bytes(b"two")

    with pytest.raises(DraftInputError, match="both be named"):
        resolve_attachments(
            [str(first), str(second)], {"scan.pdf": "x.pdf", "photo.jpg": "x.pdf"}
        )


def test_a_missing_attachment_path_is_a_usage_error(tmp_path):
    with pytest.raises(DraftInputError, match="does not exist"):
        resolve_attachments([str(tmp_path / "nope.pdf")], {})


def test_a_directory_attachment_is_a_usage_error(tmp_path):
    with pytest.raises(DraftInputError, match="not a regular file"):
        resolve_attachments([str(tmp_path)], {})


def test_an_empty_attachment_is_an_io_error(tmp_path):
    path = tmp_path / "empty.pdf"
    path.write_bytes(b"")

    with pytest.raises(DraftIoError, match="is empty"):
        resolve_attachments([str(path)], {})


def test_reply_target_replies_to_the_sender_and_prefixes_the_subject():
    target = derive_reply_target(_context(), None, reply_all=False)

    assert target.to == ["Alice Example <alice@example.com>"]
    assert target.cc == []
    assert target.subject == "Re: Klimaanlage"
    assert target.in_reply_to == "<m1@example.com>"


def test_reply_target_does_not_double_an_existing_re_prefix():
    target = derive_reply_target(_context(subject="RE: Klimaanlage"), None, False)

    assert target.subject == "RE: Klimaanlage"


def test_reply_target_chains_references_to_the_original():
    target = derive_reply_target(_context(references="<root@example.com>"), None, False)

    assert target.references == "<root@example.com> <m1@example.com>"


def test_reply_all_adds_original_recipients_but_not_the_account_itself():
    target = derive_reply_target(
        _context(
            to=["Alice Example <alice@example.com>", "me@example.com"],
            cc=["Dave <dave@example.com>", "Me <ME@example.com>"],
        ),
        "me@example.com",
        reply_all=True,
    )

    assert target.to == ["Alice Example <alice@example.com>"]
    assert target.cc == ["Dave <dave@example.com>"]


def test_reply_target_without_a_parseable_sender_is_a_usage_error():
    with pytest.raises(DraftInputError, match="cannot derive a reply recipient"):
        derive_reply_target(_context(sender=""), None, False)


def test_composed_reply_carries_the_thread_and_threading_headers():
    target = derive_reply_target(_context(), None, False)
    composed = compose_draft(
        _request(
            to=target.to,
            subject=target.subject,
            thread_id=target.thread_id,
            in_reply_to=target.in_reply_to,
            references=target.references,
        )
    )

    message = _parsed(composed)
    assert message["In-Reply-To"] == "<m1@example.com>"
    assert message["References"] == "<m1@example.com>"


def _context(**overrides) -> ReplyContext:
    fields = {
        "thread_id": "t1",
        "sender": "Alice Example <alice@example.com>",
        "to": ["me@example.com"],
        "cc": [],
        "subject": "Klimaanlage",
        "message_id_header": "<m1@example.com>",
        "references": None,
    }
    fields.update(overrides)
    return ReplyContext(**fields)


def test_reply_target_does_not_stack_a_second_prefix_on_a_german_reply():
    target = derive_reply_target(_context(subject="Aw: Abdichtung"), None, False)

    assert target.subject == "Aw: Abdichtung"
