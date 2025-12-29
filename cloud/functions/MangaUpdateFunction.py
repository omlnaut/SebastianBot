import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.services import resolve_mangaupdate_service
from cloud.functions.infrastructure.google.task import (
    task_output_binding,
)
from cloud.functions.infrastructure.google.task.models import CreateTaskEvent
from cloud.functions.infrastructure.telegram.SendTelegramMessageEvent import (
    SendTelegramMessageEvent,
)
from cloud.functions.infrastructure.telegram.helper import (
    telegram_output_binding,
)
from function_app import app
from sebastian.protocols.google_task import TaskListIds

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.MangaUpdate,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
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

        service = resolve_mangaupdate_service()
        logging.info("Checking for latest manga chapters")
        result = service.get_latest_chapters()

        logging.info(
            f"Found {len(result.item) if result.item else 0} new manga chapters"
        )

        if result.item:
            tasks = [_map_to_task_event(manga).to_output() for manga in result.item]
            taskOutput.set(tasks)  # type: ignore
            logging.info(f"Created {len(tasks)} task(s) for new manga chapters")

        if result.errors:
            logging.error(f"Errors occurred: {result.errors_string}")
            telegramOutput.set(
                SendTelegramMessageEvent(message=result.errors_string).to_output()
            )

    except Exception as e:
        error_msg = f"Error in manga_update: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())


def _map_to_task_event(manga) -> CreateTaskEvent:
    """
    Private helper to map manga data to a CreateTaskEvent.
    """
    return CreateTaskEvent(
        title=f"{manga.title} Chapter {manga.chapter}",
        notes=manga.url,
        task_list_id=TaskListIds.Mangas,
    )
