import json
from pathlib import Path

import pytest

from sebastian.clients.google.gmail.body import (
    BODY_FORMAT_HTML,
    BODY_FORMAT_TEXT,
    html_to_text,
    render_body,
    truncate,
)
from sebastian.clients.google.gmail.parsing import parse_payload

FIXTURES = Path(__file__).parent / "fixtures" / "gmail"


def _parsed(name: str):
    return parse_payload(json.loads((FIXTURES / name).read_text()))


def test_text_format_prefers_the_plain_text_part():
    parsed = _parsed("nested_related.json")

    assert render_body(parsed, BODY_FORMAT_TEXT) == "Plain body"


def test_text_format_is_the_default():
    parsed = _parsed("plain_text.json")

    assert render_body(parsed) == "Hello from plain text"


def test_text_format_falls_back_to_converted_html_for_html_only_mail():
    parsed = _parsed("html_only.json")

    assert render_body(parsed, BODY_FORMAT_TEXT) == "Hello HTML world"


def test_html_format_returns_the_raw_html_part():
    parsed = _parsed("html_only.json")

    assert (
        render_body(parsed, BODY_FORMAT_HTML)
        == "<html><body><p>Hello <b>HTML</b> world</p></body></html>"
    )


def test_html_format_falls_back_to_the_text_body_when_there_is_no_html():
    parsed = _parsed("plain_text.json")

    assert render_body(parsed, BODY_FORMAT_HTML) == "Hello from plain text"


def test_unknown_body_format_is_rejected():
    with pytest.raises(ValueError):
        render_body(_parsed("plain_text.json"), "markdown")


def test_a_body_under_the_limit_is_not_truncated():
    body, truncated = truncate("short body", 20)

    assert (body, truncated) == ("short body", False)


def test_a_body_at_the_limit_is_not_truncated():
    body, truncated = truncate("12345", 5)

    assert (body, truncated) == ("12345", False)


def test_a_body_over_the_limit_is_cut_and_flagged():
    body, truncated = truncate("0123456789", 4)

    assert (body, truncated) == ("0123", True)


def test_truncation_applies_after_the_html_fallback_rendering():
    parsed = _parsed("html_only.json")
    rendered = render_body(parsed, BODY_FORMAT_TEXT)

    body, truncated = truncate(rendered, len(html_to_text(parsed.html_body or "")) - 1)

    assert truncated is True
    assert body == rendered[:-1]
