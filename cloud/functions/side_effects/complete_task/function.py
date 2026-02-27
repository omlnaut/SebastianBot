import logging

import azure.functions as func

from cloud.dependencies import usecases
from cloud.functions.infrastructure.AllActor.helper import (
    send_all_actor_events,
)
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.functions.side_effects.shared import perform_usecase

from .models import CompleteTaskEventGrid
from function_app import app


@app.event_grid_trigger(arg_name="azeventgrid")
def complete_task(
    azeventgrid: func.EventGridEvent,
):
    def create_request(event: CompleteTaskEventGrid) -> usecases.complete_task.Request:
        return usecases.complete_task.Request(
            tasklist_id=event.tasklist_id, task_id=event.task_id
        )

    perform_usecase(
        create_request,
        usecases.resolve_complete_task,
        azeventgrid,
    )


@app.route(route="test_telegram")
def test_direct_send(req: func.HttpRequest) -> func.HttpResponse:
    """Test function that sends a telegram message via EventGrid SDK (no output binding)."""
    try:
        logging.info("Test telegram function triggered")

        # Get test message from query param or use default
        message = req.params.get("message", "Test message from HTTP trigger!")

        # Create AllActorEventGrid with a test telegram message
        actor_event = AllActorEventGrid(
            send_messages=[SendTelegramMessageEventGrid(message=message)]
        )

        send_all_actor_events([actor_event])

        logging.info(f"Test message sent: {message}")
        return func.HttpResponse(
            f"Telegram message sent successfully: {message}", status_code=200
        )

    except Exception as e:
        error_msg = f"Error sending test telegram message: {str(e)}"
        logging.error(error_msg)
        return func.HttpResponse(error_msg, status_code=500)
