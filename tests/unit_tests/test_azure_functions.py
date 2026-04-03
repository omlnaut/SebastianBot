from collections import Counter
from itertools import chain
from pathlib import Path

import astroid
from astroid.nodes import FunctionDef


# WaitForRefactor
def _get_azure_function_names(filepath: Path) -> list[str]:
    module = astroid.parse(filepath.read_text())

    target_decorator_string = "app."

    function_names: list[str] = []

    for node in module.body:
        if isinstance(node, FunctionDef) and node.decorators:
            for decorator in node.decorators.nodes:
                dec_name = decorator.as_string()
                if dec_name.startswith(target_decorator_string):
                    function_names.append(node.name)
                    break

    return function_names


def test_azure_functions_unique_names():
    paths = Path("cloud/functions").rglob("*.py")

    function_names = list(
        chain.from_iterable(_get_azure_function_names(filepath) for filepath in paths)
    )

    counts = Counter(function_names)
    duplicates = [name for name, count in counts.items() if count > 1]

    assert not duplicates, f"Duplicate Azure Function names found: {duplicates}"
