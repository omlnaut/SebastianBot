from sebastian.protocols.manga_update import (
    IMangaUpdateClient,
    MangaUpdateManga,
    MangaPublisher,
    MangaChapter,
)
from sebastian.protocols.models import AllActor, CreateTask, SendMessage
from sebastian.protocols.google_task.models import TaskListIds
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

    def get_latest_chapters(self) -> AllActor:
        tasks: list[CreateTask] = []
        errors: list[SendMessage] = []

        for manga in mangas:
            try:
                chapter = self.client.get_latest_chapter(manga)
                if is_at_most_one_day_old(chapter.release_date):
                    tasks.append(_map_to_create_task(chapter))
            except Exception as e:
                errors.append(
                    SendMessage(
                        message=f"Error fetching chapter for {manga.title}: {str(e)}"
                    )
                )

        return AllActor(create_tasks=tasks, send_messages=errors)


def _map_to_create_task(manga: MangaChapter) -> CreateTask:
    return CreateTask(
        title=f"{manga.title} Chapter {manga.chapter}",
        notes=manga.url,
        task_list_id=TaskListIds.Mangas,
    )
