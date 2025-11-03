import azure.functions as func
from pydantic import BaseModel
from typing import Type, TypeVar

T = TypeVar("T", bound=BaseModel)


def parse_payload(event: func.EventGridEvent, model: Type[T]) -> T:
    event_data = event.get_json()
    parsed_model = model.model_validate(event_data)
    return parsed_model
