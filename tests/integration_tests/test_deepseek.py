import pytest
from pydantic import BaseModel

from cloud.dependencies.clients import resolve_deepseek_client
from sebastian.clients.deepseek.client import DeepSeekClient


@pytest.fixture
def deepseek_client() -> DeepSeekClient:
    return resolve_deepseek_client()


def test_get_response(deepseek_client: DeepSeekClient):
    class JokeResponse(BaseModel):
        joke: str

    prompt = "Tell me a funny joke"
    joke_response = deepseek_client.get_response(
        prompt=prompt, response_schema=JokeResponse
    )

    assert isinstance(joke_response, JokeResponse)
    assert isinstance(joke_response.joke, str)
    assert len(joke_response.joke) > 0
