import json
from typing import TypedDict, cast

import azure.functions as func

from cloud.dependencies.usecases import resolve_ingredient_parser
from function_app import app
from sebastian.usecases.features.ingredient_parser import Request


class IngredientInput(TypedDict):
    summary: str


@app.route(route="parse_ingredients", methods=["POST"])
def parse_ingredients(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse("Request body must be a JSON array.", status_code=400)

    if not isinstance(payload, list) or any(
        not isinstance(entry, dict) or not isinstance(entry.get("summary"), str)
        for entry in payload
    ):
        return func.HttpResponse(
            "Request body must be an array of objects with a string 'summary'.",
            status_code=400,
        )

    entries = cast(list[IngredientInput], payload)
    request = Request(
        raw_ingredients=json.dumps(
            [entry["summary"] for entry in entries], ensure_ascii=False
        )
    )
    ingredients = resolve_ingredient_parser().handle(request)

    return func.HttpResponse(
        json.dumps(
            [ingredient.model_dump() for ingredient in ingredients],
            ensure_ascii=False,
        ),
        mimetype="application/json",
        status_code=200,
    )
