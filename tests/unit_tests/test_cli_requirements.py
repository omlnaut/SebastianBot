# pyright: standard
"""Keep the CLI's direct-dependency list honest.

`cli-requirements.txt` is a second dependency list: it provisions the host CLI's
dedicated virtualenv, while `pyproject.toml` stays the source of truth for the
project. These tests fail when the two drift or when the CLI starts importing
something it does not declare.
"""

import ast
import importlib.util
import re
import sys
import tomllib
from importlib.metadata import packages_distributions
from pathlib import Path

ROOT = Path(__file__).parents[2]
CLI_REQUIREMENTS = ROOT / "cli-requirements.txt"
CLI_ENTRY = ROOT / "cli" / "mail.py"
MANIFEST = ROOT / "pyproject.toml"
LOCAL_ROOTS = ("cli", "sebastian")


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _declared_requirements() -> list[str]:
    declared: list[str] = []
    for line in CLI_REQUIREMENTS.read_text().splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            declared.append(_normalize(re.match(r"[A-Za-z0-9_.-]+", entry).group(0)))
    return declared


def _manifest_dependencies() -> set[str]:
    manifest = tomllib.loads(MANIFEST.read_text())
    return {
        _normalize(name)
        for name in manifest["tool"]["poetry"]["dependencies"]
        if name != "python"
    }


def _transitive_dependencies() -> set[str]:
    """Names that any locked package depends on, so the CLI list may name them."""
    lock = tomllib.loads((ROOT / "poetry.lock").read_text())
    return {
        _normalize(name)
        for package in lock.get("package", [])
        for name in (package.get("dependencies") or {})
    }


def _dotted_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT).parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][: -len(".py")]
    return ".".join(parts)


def _module_file(dotted: str) -> Path | None:
    base = ROOT.joinpath(*dotted.split("."))
    if base.with_suffix(".py").is_file():
        return base.with_suffix(".py")
    if (base / "__init__.py").is_file():
        return base / "__init__.py"
    return None


def _imported_names(path: Path) -> list[str]:
    """Module names imported by a file, resolved to absolute dotted names."""
    dotted = _dotted_name(path)
    package = dotted if path.name == "__init__.py" else dotted.rsplit(".", 1)[0]

    names: list[str] = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = importlib.util.resolve_name("." * node.level + module, package)
            names.append(module)
            names.extend(f"{module}.{alias.name}" for alias in node.names)
    return names


def _third_party_roots(entry: Path) -> set[str]:
    """Top-level third-party import roots reachable from the CLI entry point."""
    roots: set[str] = set()
    seen: set[Path] = set()
    queue = [entry]
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)
        for name in _imported_names(path):
            module_path = _module_file(name)
            if module_path is not None:
                queue.append(module_path)
                continue
            root = name.split(".")[0]
            if root in LOCAL_ROOTS or root in sys.stdlib_module_names or not root:
                continue
            roots.add(root)
    return roots


def test_cli_requirements_carries_a_header_comment():
    first_line = CLI_REQUIREMENTS.read_text().splitlines()[0]

    assert first_line.startswith("#")
    assert "direct" in first_line.lower()


def test_declared_cli_dependencies_are_declared_or_transitive_in_the_manifest():
    allowed = _manifest_dependencies() | _transitive_dependencies()

    assert [name for name in _declared_requirements() if name not in allowed] == []


def test_declared_cli_dependencies_are_installed_in_the_project_environment():
    installed = {
        _normalize(distribution)
        for distributions in packages_distributions().values()
        for distribution in distributions
    }

    assert [name for name in _declared_requirements() if name not in installed] == []


def test_cli_dependencies_exclude_azure_and_framework_packages():
    forbidden = ("azure", "python-telegram-bot", "azure-functions")
    declared = _declared_requirements()

    assert [name for name in declared if name.split("-")[0] in forbidden] == []


def test_every_third_party_import_of_the_cli_is_a_declared_dependency():
    providers = packages_distributions()
    declared = set(_declared_requirements())

    uncovered = {
        root: sorted({_normalize(dist) for dist in providers.get(root, [])})
        for root in _third_party_roots(CLI_ENTRY)
        if not {_normalize(dist) for dist in providers.get(root, [])} & declared
    }

    assert uncovered == {}
