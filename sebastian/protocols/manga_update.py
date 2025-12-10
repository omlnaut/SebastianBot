from typing import Protocol

from sebastian.usecases.MangaUpdate.models import MangaChapter, MangaUpdateManga


class IMangaUpdateClient(Protocol):
    """Protocol for MangaUpdate client operations."""

    def get_latest_chapter(self, manga: MangaUpdateManga) -> MangaChapter:
        """Get the latest chapter for a manga from a specific publisher."""
        ...
