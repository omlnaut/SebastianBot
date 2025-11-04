import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from external.reddit.RedditClient import RedditClient
from external.reddit.RedditClientFactory import RedditClientFromSecret
from external.reddit.RedditCredentials import RedditCredentials
from external.reddit.RedditPost import RedditPost
from function_app import app
from infrastructure.google.task.TaskAzureHelper import (
    create_task_output_event,
    task_output_binding,
)
from infrastructure.google.task.TaskModels import TaskListIds
from infrastructure.google.task.TaskSchemas import CreateTaskEvent
from infrastructure.telegram.AzureHelper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from shared.dates import is_at_most_one_day_old
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

        create_task_events = [_toCreateTaskEvent(post) for post in new_chapter_posts]
        task_outputs = [create_task_output_event(event) for event in create_task_events]

        logging.info(f"Found new chapters: {new_chapter_posts}")

        if task_outputs:
            taskOutput.set(task_outputs)  # type: ignore

    except Exception as e:
        error_msg = f"Error in Skeleton Soldier function: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(create_telegram_output_event(message=error_msg))


def _toCreateTaskEvent(post: RedditPost) -> CreateTaskEvent:
    return CreateTaskEvent(
        title=f"Skeleton Soldier {post.title}",
        notes=post.destination_url,
        task_list_id=TaskListIds.Mangas,
    )
