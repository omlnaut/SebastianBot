from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel

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
        prompt = f"""You are an ingredient parser. Always respond in valid JSON format (esp. no newlines in the string): [item: str, description: str].
			Item should be the name of the ingredient, description everything else (i.e. quantity, size, color). Always respond in the same language as the input. If one ingredient is mentioned multiple times, combine the descriptions (i.e. add the weights).
			Examples:
			Input: ["1 cup of sugar", "50g Salz", "2 Stück Butter", "3/4 Liter Brühe", "20g Salz"]
			Output: [{{"item": "sugar", "description": "1 cup"}}, {{"item": "Salz", "description": "70g"}}, {{"item": "Butter", "description": "2 Stück"}}, {{"item": "Brühe", "description": "3/4 Liter"}}]
			-----
			User input: {request.raw_ingredients}
			"""

        parsed_ingredients = self._llm_client.get_response(
            prompt=prompt, response_schema=Response
        )
        return parsed_ingredients.ingredients
