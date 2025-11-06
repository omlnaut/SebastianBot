import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.services import resolve_one_punch_man_service
from cloud.functions.infrastructure.google.task import (
    CreateTaskEvent,
    task_output_binding,
)
from cloud.functions.infrastructure.telegram import (
    SendTelegramMessageEvent,
    telegram_output_binding,
)
from function_app import app
from sebastian.clients.reddit import RedditPost
from sebastian.infrastructure.google.task.models import TaskListIds


@app.timer_trigger(
    schedule="7 6 * * *", arg_name="mytimer", run_on_startup=True, use_monitor=False
)
@task_output_binding()
@telegram_output_binding()
def check_one_punch_man_updates(
    mytimer: TimerRequest,
    taskOutput: Out[EventGridOutputEvent],
    telegramOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("One Punch Man timer function started.")

        service = resolve_one_punch_man_service()
        new_chapter_posts = service.get_new_chapter_posts()

        create_task_events = [
            _to_create_task_event(post).to_output() for post in new_chapter_posts
        ]

        logging.info(f"Found new chapters: {new_chapter_posts}")

        if create_task_events:
            taskOutput.set(create_task_events)  # type: ignore

    except Exception as e:
        error_msg = f"Error in One Punch Man function: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())


def _to_create_task_event(post: RedditPost) -> CreateTaskEvent:
    return CreateTaskEvent(
        title=f"One Punch Man {post.title}",
        notes=post.destination_url or "No URL found",
        task_list_id=TaskListIds.Mangas,
    )
