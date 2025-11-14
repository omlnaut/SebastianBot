import logging

import azure.functions as func

from cloud.dependencies.services import resolve_google_task_service
from cloud.functions.infrastructure.google.helper import load_google_credentials
from cloud.functions.infrastructure.telegram.helper import (
    SendTelegramMessageEvent,
    telegram_output_binding,
)
from cloud.helper import parse_payload
from function_app import app
from sebastian.infrastructure.google.task.models import CreatedTask, TaskListIds
from sebastian.infrastructure.google.task.service import TaskService

from .helper import CreateTaskEvent, task_output_binding


@app.route(route="test_create_task")
@task_output_binding()
def test_create_task(
    req: func.HttpRequest, taskOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("HTTP test - emit create task event")

    event_model = CreateTaskEvent(
        title="Sample Task", notes="Sample notes", task_list_id=TaskListIds.Mangas
    )
    taskOutput.set(event_model.to_output())

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
@telegram_output_binding()
def create_task(
    azeventgrid: func.EventGridEvent,
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    try:
        logging.info("EventGrid create task triggered")
        event = parse_payload(azeventgrid, CreateTaskEvent)

        logging.info(f"Creating task: {event.title}")

        service = resolve_google_task_service()

        created_task = service.create_task_with_notes(
            event.task_list_id, event.title, event.notes or "", event.due
        )
        message = _build_message(created_task)

        telegramOutput.set(SendTelegramMessageEvent(message=message).to_output())

        logging.info(f"Created task: {created_task.title}")
    except Exception as e:
        error_msg = f"Error creating task: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())


def _build_message(created_task: CreatedTask) -> str:
    message = f"TASK created: {created_task.title}"
    if created_task.tasklist.name != TaskListIds.Default:
        message += f" in {created_task.tasklist.name}"
    if created_task.due:
        message += f" ({created_task.due.date()})"
    return message
