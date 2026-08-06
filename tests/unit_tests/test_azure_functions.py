from collections import Counter
from itertools import chain
from pathlib import Path

import astroid
from astroid.nodes import FunctionDef, ImportFrom

from cloud.functions.TriggerTimes import TriggerTimes


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


def test_mail_check_timer_schedule_is_10_minutes():
    assert TriggerTimes.MailCheck == "*/10 * * * *"


def test_function_app_registers_mail_check_function_import():
    module = astroid.parse(Path("function_app.py").read_text())

    imported_names: list[str] = []
    for node in module.body:
        if not isinstance(node, ImportFrom):
            continue
        if node.modname != "cloud.functions.features.mail_check_function":
            continue
        imported_names.extend(imported_name for imported_name, _ in node.names)

    assert "check_mail_check" in imported_names
