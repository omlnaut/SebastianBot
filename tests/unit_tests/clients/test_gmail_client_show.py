import json
from pathlib import Path
from typing import Any, cast

import pytest
from google.oauth2.credentials import Credentials

from sebastian.clients.google.gmail.client import client as gmail_client_module
from sebastian.clients.google.gmail.client.client import GmailClient
from sebastian.domain.gmail import GmailLabelResponse

FIXTURES = Path(__file__).parent / "fixtures" / "gmail"


class _FakeWrapper:
    """Returns one canned message; replaces the real Gmail API wrapper."""

    def __init__(self, message: dict[str, Any]):
        self._message = message

    def fetch_full_message(self, msg_id: str) -> dict[str, Any]:
        return self._message

    def list_labels(self) -> list[GmailLabelResponse]:
        return [
            GmailLabelResponse(id="INBOX", name="Inbox", type="system"),
            GmailLabelResponse(id="Label_1", name="Klima", type="user"),
        ]


def _message(payload_file: str, message_id: str = "m1") -> dict[str, Any]:
    return {
        "id": message_id,
        "threadId": "t1",
        "labelIds": ["INBOX", "Label_1"],
        "snippet": "a short snippet",
        "sizeEstimate": 48213,
        "internalDate": "1760430723000",
        "payload": json.loads((FIXTURES / payload_file).read_text()),
    }


def _client(monkeypatch: pytest.MonkeyPatch, message: dict[str, Any]) -> GmailClient:
    monkeypatch.setattr(
        gmail_client_module,
        "GmailServiceWrapper",
        lambda _credentials: _FakeWrapper(message),
    )
    return GmailClient(cast(Credentials, object()))


def test_show_returns_the_hit_shape_with_a_text_body(monkeypatch):
    client = _client(monkeypatch, _message("nested_related.json"))

    shown = client.show("m1", "text", 20000)

    assert shown.body == "Plain body"
    assert shown.body_format == "text"
    assert shown.truncated is False
    assert shown.hit.id == "m1"
    assert shown.hit.subject == "Related body"
    assert shown.hit.labels == ["Inbox", "Klima"]
    assert shown.hit.label_ids == ["INBOX", "Label_1"]


def test_show_falls_back_to_converted_html_for_html_only_mail(monkeypatch):
    client = _client(monkeypatch, _message("html_only.json"))

    shown = client.show("m1", "text", 20000)

    assert shown.body == "Hello HTML world"


def test_show_returns_raw_html_when_requested(monkeypatch):
    client = _client(monkeypatch, _message("html_only.json"))

    shown = client.show("m1", "html", 20000)

    assert shown.body_format == "html"
    assert shown.body == "<html><body><p>Hello <b>HTML</b> world</p></body></html>"


def test_show_cuts_an_over_long_body_and_flags_it(monkeypatch):
    client = _client(monkeypatch, _message("plain_text.json"))

    shown = client.show("m1", "text", 5)

    assert shown.body == "Hello"
    assert shown.truncated is True


def test_show_keeps_a_body_under_the_limit_untruncated(monkeypatch):
    client = _client(monkeypatch, _message("plain_text.json"))

    shown = client.show("m1", "text", 20000)

    assert shown.body == "Hello from plain text"
    assert shown.truncated is False


def test_show_includes_headers_and_the_attachment_list(monkeypatch):
    client = _client(monkeypatch, _message("nested_attachment.json"))

    shown = client.show("m1", "text", 20000)

    assert shown.hit.to == ["alice@example.com"]
    assert shown.hit.date == "2026-10-17T08:30:00+00:00"
    assert shown.hit.has_attachments is True
    assert [attachment.filename for attachment in shown.hit.attachments] == [
        "Rechnung.pdf"
    ]
