from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel

from sebastian.usecases.features.ingredient_parser.prompt import (
    INGREDIENT_PARSER_PROMPT,
)

T = TypeVar("T", bound=BaseModel)


@dataclass
class Request:
    raw_ingredients: str


class Ingredient(BaseModel):
    item: str
    description: str


class Response(BaseModel):
    ingredients: list[Ingredient]


class LLMClient(Protocol):
    def get_response(self, prompt: str, response_schema: type[T]) -> T: ...


class Handler:
    def __init__(self, llm_client: LLMClient):
        self._llm_client = llm_client

    def handle(self, request: Request) -> list[Ingredient]:
        prompt = INGREDIENT_PARSER_PROMPT.format(
            raw_ingredients=request.raw_ingredients
        )

        parsed_ingredients = self._llm_client.get_response(
            prompt=prompt, response_schema=Response
        )
        return parsed_ingredients.ingredients
