import json
from pathlib import Path

from sebastian.clients.google.gmail.body import html_to_text, render_text_body
from sebastian.clients.google.gmail.parsing import parse_payload
from sebastian.domain.gmail import ParsedAttachment

FIXTURES = Path(__file__).parent / "fixtures" / "gmail"


def _payload(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_plain_text_only_mail_yields_its_text_body():
    parsed = parse_payload(_payload("plain_text.json"))

    assert parsed.text_body == "Hello from plain text"
    assert parsed.html_body is None
    assert parsed.attachments == []


def test_full_header_set_is_parsed():
    parsed = parse_payload(_payload("plain_text.json"))

    assert parsed.sender == "Alice Example <alice@example.com>"
    assert parsed.to == ["Bob <bob@example.com>", "carol@example.com"]
    assert parsed.cc == ["Dave <dave@example.com>"]
    assert parsed.subject == "Plain text hello"
    assert parsed.date == "2026-10-14T09:12:03+00:00"
    assert parsed.message_id == "<abc123@example.com>"


def test_html_only_mail_falls_back_to_converted_text():
    parsed = parse_payload(_payload("html_only.json"))

    assert parsed.text_body is None
    assert parsed.html_body == "<html><body><p>Hello <b>HTML</b> world</p></body></html>"
    assert html_to_text(parsed.html_body) == "Hello HTML world"
    assert render_text_body(parsed) == "Hello HTML world"


def test_body_nested_in_related_structure_is_found():
    parsed = parse_payload(_payload("nested_related.json"))

    assert parsed.text_body == "Plain body"
    assert parsed.html_body == "<p>HTML <i>body</i></p>"
    assert render_text_body(parsed) == "Plain body"
    assert parsed.attachments == []


def test_attachment_nested_in_multipart_layout_is_discovered():
    parsed = parse_payload(_payload("nested_attachment.json"))

    assert parsed.attachments == [
        ParsedAttachment(
            filename="Rechnung.pdf",
            mime_type="application/pdf",
            size=91234,
            attachment_id="att-1",
        )
    ]


def test_inline_parts_without_a_filename_are_not_attachments():
    parsed = parse_payload(_payload("nested_related.json"))

    assert parsed.attachments == []
