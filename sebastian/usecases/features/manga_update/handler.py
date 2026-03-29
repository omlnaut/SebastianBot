from dataclasses import dataclass
from datetime import timedelta

from sebastian.domain.task import TaskLists
from sebastian.protocols.manga_update import (
    IMangaUpdateClient,
    MangaUpdateManga,
    MangaPublisher,
    MangaChapter,
)
from sebastian.protocols.models import AllActor, CreateTask, SendMessage
from sebastian.shared.dates import is_within_timedelta
from sebastian.usecases.usecase_handler import UseCaseHandler


mangas = [
    MangaUpdateManga(
        title="Omniscient Reader's Viewpoint",
        url="https://flamecomics.xyz/series/2",
        series_id=50369844984,
        publisher=MangaPublisher.FLAMECOMICS,
    ),
    MangaUpdateManga(
        title="One Piece",
        url="https://mangaplus.shueisha.co.jp/titles/100020",
        series_id=55099564912,
        publisher=MangaPublisher.MANGAPLUS,
    ),
]


@dataclass
class Request:
    time_back: timedelta


class Handler(UseCaseHandler[Request]):
    def __init__(self, client: IMangaUpdateClient):
        self.client = client

    def handle(self, request: Request) -> AllActor:
        tasks: list[CreateTask] = []
        errors: list[SendMessage] = []

        for manga in mangas:
            try:
                chapter = self.client.get_latest_chapter(manga)
                if is_within_timedelta(chapter.release_date, request.time_back):
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
        tasklist=TaskLists.Mangas,
    )
