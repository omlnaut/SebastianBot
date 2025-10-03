from pathlib import Path
import sys

root_dir = Path("/workspaces/SebastianBot")


def add_workspace_to_path():
    sys.path.insert(0, str(root_dir))
