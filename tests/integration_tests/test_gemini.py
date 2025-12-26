from pydantic import BaseModel
import pytest
from cloud.dependencies.clients import resolve_gemini_client
from sebastian.protocols.gemini import IGeminiClient


@pytest.fixture
def gemini_client() -> IGeminiClient:
    return resolve_gemini_client()


def test_get_response(gemini_client: IGeminiClient):

    class JokeResponse(BaseModel):
        joke: str

    prompt = "Tell me a funny joke in JSON format with a single field 'joke'."
    result = gemini_client.get_response(contents=prompt, response_schema=JokeResponse)

    assert not result.has_errors()
    joke_response = result.item
    assert isinstance(joke_response, JokeResponse)
    assert isinstance(joke_response.joke, str)
    assert len(joke_response.joke) > 0
