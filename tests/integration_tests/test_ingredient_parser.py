import json
from pathlib import Path

import pytest

from cloud.dependencies.usecases import resolve_ingredient_parser
from sebastian.usecases.features.ingredient_parser import Request
from sebastian.usecases.features.ingredient_parser.handler import Handler


@pytest.fixture
def ingredient_parser() -> Handler:
    return resolve_ingredient_parser()


def test_parse_example_ingredients(ingredient_parser: Handler):
    example_path = (
        Path(__file__).parents[2]
        / "sebastian/usecases/features/ingredient_parser/example_raw.json"
    )
    example_values = json.loads(example_path.read_text())

    parsed = ingredient_parser.handle(
        Request(
            raw_ingredients=json.dumps([item["summary"] for item in example_values])
        )
    )

    assert {ingredient.item.casefold() for ingredient in parsed} == {
        "mehl",
        "salz",
        "zucker",
        "butter",
        "ei",
        "zwetschgen",
        "semmelbrösel",
        "vanillezucker",
        "zimt",
    }
    descriptions = {
        ingredient.item.casefold(): ingredient.description for ingredient in parsed
    }
    assert "430" in descriptions["mehl"]
    assert "2" in descriptions["salz"]
    assert "170" in descriptions["zucker"]
    assert "250" in descriptions["butter"]
    assert "700" in descriptions["zwetschgen"]
