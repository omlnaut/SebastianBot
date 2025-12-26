from typing import TypeVar

from google import genai
from pydantic import BaseModel

from sebastian.clients.google.gemini.credentials import GeminiApiKey
from sebastian.shared.Result import Result


T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    def __init__(self, credentials: GeminiApiKey) -> None:
        self._client = genai.Client(api_key=credentials.api_key)

    def get_response(self, contents: str, response_schema: type[T]) -> Result[T]:
        """
        Generate content using Gemini model with structured output.

        Args:
            contents: The prompt/content to send to the model
            response_schema: Pydantic model class defining the expected response structure

        Returns:
            Parsed response as an instance of the response_schema type
        """
        response = self._client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            },
        )
        if isinstance(response.parsed, response_schema):
            return Result.from_item(item=response.parsed)

        return Result.from_item(
            errors=[f"Failed to parse response from Gemini model: {response.text}"]
        )
