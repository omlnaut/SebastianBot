import logging

import azure.functions as func

from cloud.dependencies import usecases

from .models import CompleteTaskEventGrid
from cloud.functions.infrastructure.telegram.models import (
    SendTelegramMessageEventGrid,
)
from cloud.functions.infrastructure.telegram.helper import (
    telegram_output_binding,
)
from cloud.helper import parse_payload
from function_app import app

# todo: sort imports


@app.event_grid_trigger(arg_name="azeventgrid")
@telegram_output_binding()
def complete_task(
    azeventgrid: func.EventGridEvent,
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    try:
        logging.info("EventGrid complete task triggered")
        event = parse_payload(azeventgrid, CompleteTaskEventGrid)

        logging.info(f"Completing task: {event.task_id} in list {event.tasklist_id}")

        request = usecases.complete_task.Request(
            tasklist_id=event.tasklist_id, task_id=event.task_id
        )
        usecase = usecases.resolve_complete_task()

        result = usecase.handle(request)

        if result.has_errors:
            error_msg = f"Error completing task: {result.errors_string}"
            logging.error(error_msg)
            telegramOutput.set(
                SendTelegramMessageEventGrid(message=error_msg).to_output()
            )

    except Exception as e:
        error_msg = f"Error completing task: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEventGrid(message=error_msg).to_output())
