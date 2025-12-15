import ast
from pathlib import Path

import pytest

# Determine repository root dynamically so CI and local runs match
# This file lives at <repo>/tests/test_imports.py, so parents[1] is the repo root
ROOT_DIR = Path(__file__).resolve().parents[1]
SEBASTIAN_DIR = ROOT_DIR / "sebastian"
CLOUD_DIR = ROOT_DIR / "cloud"
PROTOCOLS_DIR = SEBASTIAN_DIR / "protocols"

# Collect python files under sebastian once to avoid empty parameter set skips
_SEBASTIAN_PY_FILES = [
    str(p.relative_to(SEBASTIAN_DIR)) for p in SEBASTIAN_DIR.rglob("*.py")
]

# Collect python files under protocols
_PROTOCOLS_PY_FILES = [
    str(p.relative_to(PROTOCOLS_DIR)) for p in PROTOCOLS_DIR.rglob("*.py")
]


def test_sebastian_contains_python_files():
    """Ensure we found files; prevents empty parameter set being marked as skipped."""
    assert len(_SEBASTIAN_PY_FILES) > 0, f"No Python files found under {SEBASTIAN_DIR}"


def test_protocols_contains_python_files():
    """Ensure we found files; prevents empty parameter set being marked as skipped."""
    assert len(_PROTOCOLS_PY_FILES) > 0, f"No Python files found under {PROTOCOLS_DIR}"


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


@pytest.mark.parametrize("file_path", _PROTOCOLS_PY_FILES)
def test_protocols_no_external_imports(file_path: str):
    """Ensure protocol files only import from within protocols module or standard/external libraries."""
    content = (PROTOCOLS_DIR / file_path).read_text()
    tree = ast.parse(content, filename=file_path)

    # Allowed sebastian imports are only from protocols
    allowed_sebastian_prefix = "sebastian.protocols."
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Check if importing from sebastian but not from protocols
                if alias.name.startswith("sebastian.") and not alias.name.startswith(allowed_sebastian_prefix):
                    assert False, f"protocols/{file_path} imports {alias.name} from outside protocols module"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Check if importing from sebastian but not from protocols
                if node.module.startswith("sebastian.") and not node.module.startswith(allowed_sebastian_prefix):
                    assert False, f"protocols/{file_path} imports from {node.module} outside protocols module"

