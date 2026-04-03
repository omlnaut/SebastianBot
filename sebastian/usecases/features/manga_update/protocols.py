from typing import Protocol

from sebastian.domain.mangas import MangaChapter, MangaUpdateManga

__all__ = ["MangaUpdateClient"]


class MangaUpdateClient(Protocol):
    """Protocol for MangaUpdate client operations."""

    def get_latest_chapter(self, manga: MangaUpdateManga) -> MangaChapter:
        """Get the latest chapter for a manga from a specific publisher."""
        ...
