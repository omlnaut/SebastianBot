import pytest
from pydantic import BaseModel

from cloud.dependencies.clients import resolve_gemini_client
from sebastian.clients.google.gemini.client import GeminiClient


@pytest.fixture
def gemini_client() -> GeminiClient:
    return resolve_gemini_client()


def test_get_response(gemini_client: GeminiClient):
    class JokeResponse(BaseModel):
        joke: str

    prompt = "Tell me a funny joke in JSON format with a single field 'joke'."
    joke_response = gemini_client.get_response(
        prompt=prompt, response_schema=JokeResponse
    )

    assert isinstance(joke_response, JokeResponse)
    assert isinstance(joke_response.joke, str)
    assert len(joke_response.joke) > 0
