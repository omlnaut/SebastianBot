from typing import TypeVar

from google import genai
from pydantic import BaseModel

from sebastian.clients.google.gemini.credentials import GeminiApiKey
from sebastian.usecases.shared.gemini_exceptions import (
    NonRetryableGeminiError,
    TransientGeminiError,
)

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """
    See https://ai.google.dev/gemini-api/docs/rate-limits
    """

    def __init__(self, credentials: GeminiApiKey) -> None:
        self._client = genai.Client(api_key=credentials.api_key)

    def _is_transient_error(self, error: Exception) -> bool:
        text = str(error).lower()
        transient_markers = [
            "overloaded",
            "resource exhausted",
            "resource_exhausted",
            "rate limit",
            "429",
            "service unavailable",
            "temporarily unavailable",
            "try again later",
            "deadline exceeded",
            "timeout",
            "unavailable",
        ]
        return any(marker in text for marker in transient_markers)

    def get_response(self, prompt: str, response_schema: type[T]) -> T:
        """
        Generate content using Gemini model with structured output.

        Args:
            contents: The prompt/content to send to the model
            response_schema: Pydantic model class defining the expected response structure

        Returns:
            Parsed response as an instance of the response_schema type
        """
        try:
            response = self._client.interactions.create(
                model="gemini-3.5-flash",
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": response_schema.model_json_schema(),
                },
            )
            return response_schema.model_validate_json(response.output_text)  # type: ignore
        except Exception as e:
            if self._is_transient_error(e):
                raise TransientGeminiError(str(e)) from e
            raise NonRetryableGeminiError(str(e)) from e
