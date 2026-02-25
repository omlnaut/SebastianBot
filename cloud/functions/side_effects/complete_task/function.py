import logging

import azure.functions as func

from azure.functions import EventGridOutputEvent, Out

from cloud.dependencies import usecases
from cloud.functions.infrastructure.AllActor.helper import all_actor_output_binding
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid

from .models import CompleteTaskEventGrid
from cloud.functions.infrastructure.telegram.models import (
    SendTelegramMessageEventGrid,
)
from cloud.helper import parse_payload
from function_app import app

# todo: sort imports


@app.event_grid_trigger(arg_name="azeventgrid")
@all_actor_output_binding()
def complete_task(
    azeventgrid: func.EventGridEvent,
    allActorOutput: Out[EventGridOutputEvent],
):
    try:
        logging.info("EventGrid complete task triggered")
        event = parse_payload(azeventgrid, CompleteTaskEventGrid)

        logging.info(f"Completing task: {event.task_id} in list {event.tasklist_id}")

        request = usecases.complete_task.Request(
            tasklist_id=event.tasklist_id, task_id=event.task_id
        )
        usecase = usecases.resolve_complete_task()

        actor_result = usecase.handle(request)

        allActorOutput.set(AllActorEventGrid.from_application(actor_result).to_output())

    except Exception as e:
        error_msg = f"Error completing task: {str(e)}"
        logging.error(error_msg)
        allActorOutput.set(
            AllActorEventGrid(
                send_messages=[SendTelegramMessageEventGrid(message=error_msg)]
            ).to_output()
        )


# todo: refactor to general perform_usecase
