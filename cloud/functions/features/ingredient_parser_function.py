import json

import azure.functions as func

from cloud.dependencies.usecases import resolve_ingredient_parser
from function_app import app
from sebastian.usecases.features.ingredient_parser import Request


@app.route(route="parse_ingredients", methods=["POST"])
def parse_ingredients(req: func.HttpRequest) -> func.HttpResponse:
    request = Request(raw_ingredients=req.get_body().decode("utf-8"))
    ingredients = resolve_ingredient_parser().handle(request)

    return func.HttpResponse(
        json.dumps(
            [ingredient.model_dump() for ingredient in ingredients],
            ensure_ascii=False,
        ),
        mimetype="application/json",
        status_code=200,
    )
