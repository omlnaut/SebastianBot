import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies import RedditClientFromSecret
from cloud.functions.infrastructure.google.task.helper import (
    CreateTaskEvent,
    task_output_binding,
)
from cloud.functions.infrastructure.telegram import telegram_output_binding
from cloud.functions.infrastructure.telegram.helper import SendTelegramMessageEvent
from function_app import app
from sebastian.clients.reddit import RedditPost
from sebastian.infrastructure.google.task.models import TaskListIds
from usecases.manga.skeleton_soldier.SkeletonSolderService import is_new_chapter_post


@app.timer_trigger(
    schedule="4 3 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False
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

        reddit_client = RedditClientFromSecret()
        posts = reddit_client.get_posts("SkeletonSoldier")

        new_chapter_posts = [post for post in posts if is_new_chapter_post(post)]

        create_task_events = [
            _toCreateTaskEvent(post).to_output() for post in new_chapter_posts
        ]

        logging.info(f"Found new chapters: {new_chapter_posts}")

        if create_task_events:
            taskOutput.set(create_task_events)  # type: ignore

    except Exception as e:
        error_msg = f"Error in Skeleton Soldier function: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())


def _toCreateTaskEvent(post: RedditPost) -> CreateTaskEvent:
    return CreateTaskEvent(
        title=f"Skeleton Soldier {post.title}",
        notes=post.destination_url,
        task_list_id=TaskListIds.Mangas,
    )
