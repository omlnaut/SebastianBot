from datetime import date
from pathlib import Path

import pytest

from cloud.dependencies.clients import resolve_gemini_client
from sebastian.usecases.features.delivery_ready.parsing import (
    parse_dhl_pickup_email_html,
)
from sebastian.usecases.features.delivery_ready.protocols import GeminiClient


@pytest.fixture
def gemini_client() -> GeminiClient:
    return resolve_gemini_client()


def test_parsing(gemini_client: GeminiClient):
    html = (Path(__file__).parent / "delivery_ready_example.html").read_text()

    parsed = parse_dhl_pickup_email_html(html, gemini_client)

    assert parsed.tracking_number == "JJD000390016898240196"
    assert parsed.pickup_location == "Packstation 158"
    assert parsed.due_date == date(2026, 3, 31)
    assert "Medela" in parsed.item
