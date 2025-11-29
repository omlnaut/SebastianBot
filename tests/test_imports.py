import ast
from pathlib import Path

import pytest

# Determine repository root dynamically so CI and local runs match
# This file lives at <repo>/tests/test_imports.py, so parents[2] is the repo root
ROOT_DIR = Path(__file__).resolve().parents[1]
SEBASTIAN_DIR = ROOT_DIR / "sebastian"
CLOUD_DIR = ROOT_DIR / "cloud"

# Collect python files under sebastian once to avoid empty parameter set skips
_SEBASTIAN_PY_FILES = [
    str(p.relative_to(SEBASTIAN_DIR)) for p in SEBASTIAN_DIR.rglob("*.py")
]


def test_sebastian_contains_python_files():
    """Ensure we found files; prevents empty parameter set being marked as skipped."""
    assert len(_SEBASTIAN_PY_FILES) > 0, f"No Python files found under {SEBASTIAN_DIR}"


@pytest.mark.parametrize("file_path", _SEBASTIAN_PY_FILES)
def test_no_import_from_cloud(file_path: str):
    """Ensure no file in sebastian imports anything from cloud."""
    content = (SEBASTIAN_DIR / file_path).read_text()
    tree = ast.parse(content, filename=file_path)
    cloud_import = "cloud."

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(
                    cloud_import
                ), f"{file_path} imports {alias.name} from {CLOUD_DIR}"
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(cloud_import):
                assert False, f"{file_path} imports from {node.module} in {CLOUD_DIR}"
