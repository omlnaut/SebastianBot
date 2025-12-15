from sebastian.protocols.manga_update import (
    IMangaUpdateClient,
    MangaUpdateManga,
    MangaPublisher,
    MangaChapter,
)
from sebastian.shared import Result
from sebastian.shared.dates import is_at_most_one_day_old


mangas = [
    MangaUpdateManga(
        title="Omniscient Reader's Viewpoint",
        url="https://flamecomics.xyz/series/2",
        series_id=50369844984,
        publisher=MangaPublisher.FLAMECOMICS,
    ),
    MangaUpdateManga(
        title="Auto Hunting with Clones",
        url="https://flamecomics.xyz/series/109",
        series_id=44327338345,
        publisher=MangaPublisher.FLAMECOMICS,
    ),
    MangaUpdateManga(
        title="One Piece",
        url="https://mangaplus.shueisha.co.jp/titles/100020",
        series_id=55099564912,
        publisher=MangaPublisher.MANGAPLUS,
    ),
]


class MangaUpdateService:
    def __init__(self, client: IMangaUpdateClient):
        self.client = client

    def get_latest_chapters(self) -> Result[list[MangaChapter]]:
        chapters: list[MangaChapter] = []
        errors: list[str] = []

        for manga in mangas:
            try:
                chapter = self.client.get_latest_chapter(manga)
                if is_at_most_one_day_old(chapter.release_date):
                    chapters.append(chapter)
            except Exception as e:
                errors.append(f"Error fetching chapter for {manga.title}: {str(e)}")

        return Result.from_item(item=chapters, errors=errors)
