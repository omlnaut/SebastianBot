from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MangaPublisher(Enum):
    """Publisher id (called group_id on MangaUpdate API). Go to publisher page in browser and search for "group_id"."""

    FLAMECOMICS = 57949066600
    MANGAPLUS = 49204242348


@dataclass
class MangaUpdateManga:
    title: str
    url: str
    series_id: int
    publisher: MangaPublisher


@dataclass
class MangaChapter:
    chapter: str
    release_date: datetime
    title: str
