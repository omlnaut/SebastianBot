from datetime import datetime
import logging
import uuid
import azure.functions as func
from cloud.functions.infrastructure.AllHandler.models import AllHandlerEventGrid
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.functions.side_effects.create_task.models import CreateTaskEventGrid
from cloud.functions.side_effects.shared import send_eventgrid_events
from cloud.helper.parsing import parse_payload
from function_app import app


@app.route(route="test_trigger_allhandler")
def test_trigger_allhandler(
    req: func.HttpRequest,
) -> func.HttpResponse:
    logging.info("HTTP test - emit trigger all handler event")

    base_event = AllHandlerEventGrid(
        create_task_events=[CreateTaskEventGrid(title="Test Task from AllHandler")],
    )

    send_eventgrid_events([base_event])

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
def all_handler(
    azeventgrid: func.EventGridEvent,
):
    try:
        logging.info("AllHandler triggered")
        telegram_messages = [
            SendTelegramMessageEventGrid(message="AllHandler triggered")
        ]

        payload = parse_payload(azeventgrid, AllHandlerEventGrid)

        # wip, just send telegram messages for now
        # will get removed later
        for archive_email_event in payload.archive_email_events:
            message = SendTelegramMessageEventGrid(
                message=f"Email to be archived: {archive_email_event.title}",
            )
            telegram_messages.append(message)

        for mark_to_read_event in payload.put_email_in_to_read_events:
            message = SendTelegramMessageEventGrid(
                message=f"Email to be marked as to-read: {mark_to_read_event.title}",
            )
            telegram_messages.append(message)

        for task_event in payload.create_task_events:
            message = SendTelegramMessageEventGrid(
                message=f"Task to be created: {task_event.title}: {task_event.notes or 'No notes'} at {task_event.due or 'No due date'}",
            )
            telegram_messages.append(message)

        if telegram_messages:
            send_eventgrid_events(telegram_messages)

        logging.info("AllHandler completed")

    except Exception as e:
        error_msg = f"Error in all_handler: {str(e)}"
        logging.error(error_msg)
        send_eventgrid_events([SendTelegramMessageEventGrid(message=error_msg)])
