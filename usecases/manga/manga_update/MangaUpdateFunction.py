import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.functions.infrastructure.google.task.helper import (
    CreateTaskEvent,
    task_output_binding,
)
from cloud.functions.infrastructure.telegram import telegram_output_binding
from cloud.functions.infrastructure.telegram.helper import SendTelegramMessageEvent
from function_app import app
from sebastian.infrastructure.google.task.models import TaskListIds
from shared.dates import is_at_most_one_day_old
from usecases.manga.manga_update.MangaModels import MangaPublisher, MangaUpdateManga
from usecases.manga.manga_update.MangaUpdateService import MangaUpdateService

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


@app.timer_trigger(
    schedule="7 3 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False
)
@task_output_binding()
@telegram_output_binding()
def check_manga_update(
    mytimer: TimerRequest,
    taskOutput: Out[EventGridOutputEvent],
    telegramOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("MangaUpdate timer function processed a request.")

        service = MangaUpdateService()

        tasks, messages = _check_all_manga(service)

        if tasks:
            taskOutput.set(tasks)  # type: ignore

        if messages:
            telegramOutput.set(messages)  # type: ignore

    except Exception as e:
        error_msg = f"Error in manga_update: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())


def _check_all_manga(
    service,
) -> tuple[list[EventGridOutputEvent], list[EventGridOutputEvent]]:
    tasks: list[EventGridOutputEvent] = []
    messages: list[EventGridOutputEvent] = []

    for manga in mangas:
        try:
            latest_chapter = service.get_latest_chapter(manga)
            logging.info(
                f"Latest chapter for {manga.title}: Chapter {latest_chapter.chapter} ({latest_chapter.release_date.strftime('%Y-%m-%d')})"
            )

            if is_at_most_one_day_old(latest_chapter.release_date):
                tasks.append(
                    CreateTaskEvent(
                        title=f"{manga.title} Chapter {latest_chapter.chapter}",
                        notes=manga.url,
                        task_list_id=TaskListIds.Mangas,
                    ).to_output()
                )

                logging.info(
                    f"Created task for {manga.title} Chapter {latest_chapter.chapter}"
                )

        except Exception as e:
            error_msg = f"Failed to process manga {manga.title}: {str(e)}"
            logging.error(error_msg)
            messages.append(SendTelegramMessageEvent(message=error_msg).to_output())
    return tasks, messages
