from typing import Protocol, TypeVar

from pydantic import BaseModel

from sebastian.shared.Result import Result


T = TypeVar("T", bound=BaseModel)


class IGeminiClient(Protocol):
    def get_response(self, contents: str, response_schema: type[T]) -> Result[T]:
        """
        Generate content using Gemini model with structured output.

        Args:
            contents: The prompt/content to send to the model
            response_schema: Pydantic model class defining the expected response structure

        Returns:
            Parsed response as an instance of the response_schema type
        """
        ...
