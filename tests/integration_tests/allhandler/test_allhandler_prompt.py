from pathlib import Path

import pytest
from cloud.dependencies.clients import resolve_gemini_client
from sebastian.protocols.gemini.IClient import IGeminiClient
from sebastian.usecases.AllHandler.prompt_builder import build_prompt, clean_html_tags
from sebastian.usecases.AllHandler.prompt_models import AllHandlerEvent


TEST_CONTENT_PATH = Path(__file__).parent / "test_content"


@pytest.fixture
def gemini() -> IGeminiClient:
    return resolve_gemini_client()


@pytest.mark.parametrize(
    "html_filename",
    ["make_new_appointment.html", "fetch_recipe.html", "tk_message.html"],
)
def test_prompt_create_task(gemini: IGeminiClient, html_filename: str):
    html_file = TEST_CONTENT_PATH / html_filename
    html_content = html_file.read_text()

    text_content = clean_html_tags(html_content)
    prompt = build_prompt(text_content)

    result = gemini.get_response(prompt, AllHandlerEvent)

    assert not result.has_errors()

    event = result.item

    assert event is not None
    assert len(event.create_task_events) == 1
    assert len(event.archive_email_events) == 0
    assert len(event.put_email_in_to_read_events) == 0


@pytest.mark.parametrize(
    "html_filename",
    [
        "linked_jobs.html",
    ],
)
def test_prompt_to_read(gemini: IGeminiClient, html_filename: str):
    html_file = TEST_CONTENT_PATH / html_filename
    html_content = html_file.read_text()

    text_content = clean_html_tags(html_content)
    prompt = build_prompt(text_content)

    result = gemini.get_response(prompt, AllHandlerEvent)

    assert not result.has_errors()

    event = result.item

    assert event is not None
    assert len(event.create_task_events) == 0
    assert len(event.archive_email_events) == 0
    assert len(event.put_email_in_to_read_events) == 1
