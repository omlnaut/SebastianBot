import logging

from function_app import app
import azure.functions as func

from infrastructure.google.task.TaskService import TaskService, TaskListIds
from infrastructure.google.task.TaskAzureHelper import (
    create_task_output_event,
    task_output_binding,
)
from infrastructure.google.task.TaskSchemas import CreateTaskEvent
from infrastructure.google.GoogleSecret import GoogleSecret
from infrastructure.telegram.AzureHelper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from shared.secrets import get_secret, SecretKeys
from google.oauth2.credentials import Credentials


@app.route(route="test_create_task")
@task_output_binding()
def test_create_task(
    req: func.HttpRequest, taskOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("HTTP test - emit create task event")

    event_model = CreateTaskEvent(title="Sample Task", notes="Sample notes")
    taskOutput.set(create_task_output_event(event_model))

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
@telegram_output_binding()
def create_task(
    azeventgrid: func.EventGridEvent,
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    logging.info("EventGrid create task triggered")
    payload = azeventgrid.get_json()

    try:
        event = CreateTaskEvent.model_validate(payload)
    except Exception as e:
        logging.error(f"Failed to parse event payload: {e}")
        return

    credentials_model = get_secret(SecretKeys.GoogleCredentials, GoogleSecret)
    creds = Credentials.from_authorized_user_info(
        credentials_model.credentials.model_dump()
    )

    service = TaskService(creds)
    created_task = service.create_task_with_notes(
        TaskListIds.Default, event.title, event.notes or "", event.due
    )
    telegramOutput.set(
        create_telegram_output_event(
            f"TASK created: {created_task.title} ({created_task.due.date()})"
        )
    )

    logging.info(f"Created task: {created_task.title}")
