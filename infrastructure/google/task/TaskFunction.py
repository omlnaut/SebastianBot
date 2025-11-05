import logging

import azure.functions as func

from cloud.functions.infrastructure.telegram import telegram_output_binding
from cloud.functions.infrastructure.telegram.helper import SendTelegramMessageEvent
from cloud.helper import parse_payload
from function_app import app
from infrastructure.google.GoogleAzureHelper import load_google_credentials
from infrastructure.google.task.TaskAzureHelper import (
    create_task_output_event,
    task_output_binding,
)
from infrastructure.google.task.TaskSchemas import CreateTaskEvent
from infrastructure.google.task.TaskService import TaskListIds, TaskService


@app.route(route="test_create_task")
@task_output_binding()
def test_create_task(
    req: func.HttpRequest, taskOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("HTTP test - emit create task event")

    event_model = CreateTaskEvent(
        title="Sample Task", notes="Sample notes", task_list_id=TaskListIds.Mangas
    )
    taskOutput.set(create_task_output_event(event_model))

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
@telegram_output_binding()
def create_task(
    azeventgrid: func.EventGridEvent,
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    logging.info("EventGrid create task triggered")
    event = parse_payload(azeventgrid, CreateTaskEvent)

    creds = load_google_credentials()
    service = TaskService(creds)

    created_task = service.create_task_with_notes(
        event.task_list_id, event.title, event.notes or "", event.due
    )
    telegramOutput.set(
        SendTelegramMessageEvent(
            message=f"TASK created: {created_task.title} in {created_task.tasklist.name} ({created_task.due.date()})"
        ).to_output()
    )

    logging.info(f"Created task: {created_task.title}")
