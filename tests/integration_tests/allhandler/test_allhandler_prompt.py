from pathlib import Path

import pytest
from cloud.dependencies.clients import resolve_gemini_client
from cloud.functions.infrastructure.AllHandler.models import AllHandlerEvent
from sebastian.protocols.gemini.IClient import IGeminiClient
from sebastian.usecases.AllHandler.prompt_builder import build_prompt, clean_html_tags


TEST_CONTENT_PATH = Path(__file__).parent / "test_content"


@pytest.fixture
def gemini() -> IGeminiClient:
    return resolve_gemini_client()


def test_build_prompt_make_new_appointment(gemini: IGeminiClient):
    html_file = TEST_CONTENT_PATH / "make_new_appointment.html"
    html_content = html_file.read_text()

    text_content = clean_html_tags(html_content)
    prompt = build_prompt(text_content)

    result = gemini.get_response(prompt, AllHandlerEvent)

    assert not result.has_errors()

    event = result.item

    assert event is not None
    assert len(event.create_task_events) == 1
    assert len(event.send_telegram_message_events) == 0


def test_build_prompt_fetch_recipe(gemini: IGeminiClient):
    html_file = TEST_CONTENT_PATH / "fetch_recipe.html"
    html_content = html_file.read_text()

    text_content = clean_html_tags(html_content)
    prompt = build_prompt(text_content)

    result = gemini.get_response(prompt, AllHandlerEvent)

    assert not result.has_errors()

    event = result.item

    assert event is not None
    assert len(event.create_task_events) == 1
    assert len(event.send_telegram_message_events) == 0
