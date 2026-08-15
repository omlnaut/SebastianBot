from datetime import date
from pathlib import Path

import pytest

from cloud.dependencies.clients import resolve_deepseek_client
from sebastian.usecases.features.delivery_ready.parsing import (
    parse_dhl_pickup_email_html,
)
from sebastian.usecases.features.delivery_ready.protocols import LLMClient


@pytest.fixture
def llm_client() -> LLMClient:
    return resolve_deepseek_client()


def test_parsing(llm_client: LLMClient):
    html = (Path(__file__).parent / "delivery_ready_example.html").read_text()

    parsed = parse_dhl_pickup_email_html(html, llm_client)

    assert parsed.tracking_number == "JJD000390016898240196"
    assert parsed.pickup_location == "Packstation 158"
    assert parsed.due_date == date(2026, 3, 31)
    assert "Medela" in parsed.item
