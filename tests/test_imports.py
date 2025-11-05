import ast
import os
from pathlib import Path

import pytest

# Define the directory to check
ROOT_DIR = Path("/workspaces/SebastianBot")
SEBASTIAN_DIR = ROOT_DIR / "sebastian"
CLOUD_DIR = ROOT_DIR / "cloud"


@pytest.mark.parametrize(
    "file_path",
    [(str(file.relative_to(SEBASTIAN_DIR))) for file in SEBASTIAN_DIR.rglob("*.py")],
)
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
