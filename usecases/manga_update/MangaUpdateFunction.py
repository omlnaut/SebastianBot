import logging
from datetime import datetime
from pathlib import Path

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from infrastructure.google.task.TaskAzureHelper import create_task_output_event
from infrastructure.google.task.TaskModels import TaskListIds
from infrastructure.google.task.TaskSchemas import CreateTaskEvent
from infrastructure.telegram.AzureHelper import create_telegram_output_event
from shared.dates import is_at_most_one_day_old
from usecases.manga_update.MangaModels import MangaPublisher, MangaUpdateManga
from usecases.manga_update.MangaUpdateService import MangaUpdateService

mangas = [
    MangaUpdateManga(
        title="Omniscient Reader's Viewpoint",
        url="https://flamecomics.xyz/series/2",
        series_id=50369844984,
        publisher=MangaPublisher.FLAMECOMICS,
    )
]


def check_manga_update(
    mytimer: TimerRequest,
    taskOutput: Out[EventGridOutputEvent],
    telegramOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("MangaUpdate timer function processed a request.")

        service = MangaUpdateService()

        tasks: list[EventGridOutputEvent] = []
        for manga in mangas:
            try:
                latest_chapter = service.get_latest_chapter(manga)
                logging.info(
                    f"Latest chapter for {manga.title}: Chapter {latest_chapter.chapter} ({latest_chapter.release_date.strftime('%Y-%m-%d')})"
                )

                if is_at_most_one_day_old(latest_chapter.release_date):
                    tasks.append(
                        create_task_output_event(
                            event=CreateTaskEvent(
                                title=f"{manga.title} Chapter {latest_chapter.chapter}",
                                notes=manga.url,
                                task_list_id=TaskListIds.Mangas,
                            )
                        )
                    )

                    logging.info(
                        f"Created task for {manga.title} Chapter {latest_chapter.chapter}"
                    )

            except Exception as e:
                error_msg = f"Failed to process manga {manga.title}: {str(e)}"
                logging.error(error_msg)
                tasks.append(create_telegram_output_event(message=error_msg))

        if tasks:
            taskOutput.set(tasks)  # type: ignore
    except Exception as e:
        error_msg = f"Error in manga_update: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(create_telegram_output_event(message=error_msg))
