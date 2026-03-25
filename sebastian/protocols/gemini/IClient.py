from typing import Protocol, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class IGeminiClient(Protocol):
    def get_response(self, prompt: str, response_schema: type[T]) -> T:
        """
        Generate content using Gemini model with structured output.

        Args:
            prompt: The prompt/content to send to the model
            response_schema: Pydantic model class defining the expected response structure

        Returns:
            Parsed response as an instance of the response_schema type
        """
        ...
