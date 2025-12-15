from typing import Generator, Protocol

from .models import Folder


class IMietplanClient(Protocol):
    """Protocol for Mietplan client operations."""

    def walk_from_top_folder(self) -> Generator[Folder, None, None]:
        """Walk through all folders starting from the top folder."""
        ...

    def download_file(self, download_path: str) -> bytes:
        """Download a file from the given path."""
        ...
