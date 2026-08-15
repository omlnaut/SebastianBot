import requests

from sebastian.clients.deepseek.credentials import DeepSeekApiKey
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class DeepSeekClient:
    BASE_URL = "https://api.deepseek.com/chat/completions"

    def __init__(self, credentials: DeepSeekApiKey) -> None:
        self._api_key = credentials.api_key

    def get_response(self, prompt: str, response_schema: type[T]) -> T:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        payload = {
            "model": "deepseek-v4-flash",
            "messages": [
                {
                    "role": "system",
                    "content": f"Return only valid JSON with the schema {response_schema.model_json_schema()}",
                },
                {"role": "user", "content": prompt},
            ],
            "thinking": {"type": "disabled"},
            "reasoning_effort": "high",
            "response_format": {"type": "json_object"},
            "stream": False,
        }

        response = requests.post(
            self.BASE_URL, headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()
        return response_schema.model_validate_json(
            response.json()["choices"][0]["message"]["content"]
        )
