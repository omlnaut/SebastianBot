import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.services import resolve_skeleton_soldier_service
from cloud.functions.infrastructure.google.task import (
    CreateTaskEvent,
    task_output_binding,
)
from cloud.functions.infrastructure.telegram.helper import (
    SendTelegramMessageEvent,
    telegram_output_binding,
)
from function_app import app
from sebastian.protocols.reddit import RedditPost
from sebastian.protocols.google_task import TaskListIds
from sebastian.protocols.reddit.models import RedditComment

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.SkeletonSoldier,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@task_output_binding()
@telegram_output_binding()
def check_skeleton_soldier_updates(
    mytimer: TimerRequest,
    taskOutput: Out[EventGridOutputEvent],
    telegramOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("Skeleton Soldier timer function started.")

        service = resolve_skeleton_soldier_service()
        logging.info("Checking for new Skeleton Soldier chapters")
        new_chapter_comments = service.get_new_chapter_comments()

        logging.info(f"Found {len(new_chapter_comments)} new chapter(s)")

        create_task_events = [
            _to_create_task_event().to_output() for comment in new_chapter_comments
        ]

        if create_task_events:
            taskOutput.set(create_task_events)  # type: ignore
            logging.info(f"Created {len(create_task_events)} task(s) for new chapters")

    except Exception as e:
        error_msg = f"Error in Skeleton Soldier function: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())


def _to_create_task_event() -> CreateTaskEvent:
    return CreateTaskEvent(
        title=f"Skeleton Soldier",
        notes="https://demonicscans.org/manga/Skeleton-Soldier",
        task_list_id=TaskListIds.Mangas,
    )
