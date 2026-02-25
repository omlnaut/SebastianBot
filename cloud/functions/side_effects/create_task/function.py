import logging

import azure.functions as func

from cloud.dependencies import usecases
from cloud.functions.infrastructure.AllActor.helper import all_actor_output_binding
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid


from .models import CreateTaskEventGrid
from cloud.functions.infrastructure.telegram.models import (
    SendTelegramMessageEventGrid,
)
from cloud.functions.infrastructure.telegram.helper import (
    telegram_output_binding,
)
from azure.functions import EventGridOutputEvent, Out
from cloud.helper import parse_payload
from function_app import app
from sebastian.protocols.google_task import CreatedTask, TaskListIds

from .helper import task_output_binding


@app.route(route="test_create_task")
@task_output_binding()
def test_create_task(
    req: func.HttpRequest, taskOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("HTTP test - emit create task event")

    event_model = CreateTaskEventGrid(
        title="Sample Task", notes="Sample notes", task_list_id=TaskListIds.Mangas
    )
    taskOutput.set(event_model.to_output())

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
@all_actor_output_binding()
def create_task(
    azeventgrid: func.EventGridEvent,
    allActorOutput: Out[EventGridOutputEvent],
):
    try:
        logging.info("EventGrid create task triggered")
        event = parse_payload(azeventgrid, CreateTaskEventGrid)

        logging.info(f"Creating task: {event.title}")

        request = usecases.create_task.Request(
            tasklist_id=event.task_list_id,
            title=event.title,
            notes=event.notes or "",
            due_date=event.due,
        )
        usecase = usecases.resolve_create_task()

        actor_result = usecase.handle(request)

        allActorOutput.set(AllActorEventGrid.from_application(actor_result).to_output())

    except Exception as e:
        error_msg = f"Error creating task: {str(e)}"
        logging.error(error_msg)
        allActorOutput.set(
            AllActorEventGrid(
                send_messages=[SendTelegramMessageEventGrid(message=error_msg)]
            ).to_output()
        )


def _build_message(created_task: CreatedTask) -> str:
    message = f"TASK created: {created_task.title}"
    if created_task.tasklist.name != TaskListIds.Default.name:
        message += f" in {created_task.tasklist.name}"
    if created_task.due:
        message += f" ({created_task.due.date()})"
    if created_task.webViewLink:
        message += f"\n{created_task.webViewLink}"
    return message
