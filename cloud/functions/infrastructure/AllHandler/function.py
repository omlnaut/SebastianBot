from datetime import datetime
import logging
import uuid
import azure.functions as func
from cloud.functions.infrastructure.AllHandler.helper import allhandler_output_binding
from cloud.functions.infrastructure.AllHandler.models import AllHandlerEvent
from cloud.functions.infrastructure.google.task.models import CreateTaskEvent
from cloud.functions.infrastructure.telegram.helper import telegram_output_binding
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEvent
from cloud.helper.parsing import parse_payload
from function_app import app


@app.route(route="test_trigger_allhandler")
@allhandler_output_binding()
def test_trigger_allhandler(
    req: func.HttpRequest, allHandlerOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("HTTP test - emit trigger all handler event")

    base_event = AllHandlerEvent(
        create_task_events=[CreateTaskEvent(title="Test Task from AllHandler")],
        send_telegram_message_events=[
            SendTelegramMessageEvent(message="Test Message from AllHandler")
        ],
    )

    allHandlerOutput.set(base_event.to_output())

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
@telegram_output_binding()
def all_handler(
    azeventgrid: func.EventGridEvent,
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    logging.info("AllHandler triggered")

    payload = parse_payload(azeventgrid, AllHandlerEvent)

    # wip, just send telegram messages for now
    # will get removed later
    telegram_messages = []
    for telegram_event in payload.send_telegram_message_events:
        telegram_event.message += "\n\n(From AllHandler)"
        telegram_messages.append(telegram_event.to_output())

    for task_event in payload.create_task_events:
        message = SendTelegramMessageEvent(
            message=f"Task to be created: {task_event.title}: {task_event.notes or 'No notes'} at {task_event.due or 'No due date'}",
        )
        telegram_messages.append(message.to_output())

    if telegram_messages:
        telegramOutput.set(telegram_messages)  # type: ignore

    telegramOutput.set(
        SendTelegramMessageEvent(message="AllHandler triggered").to_output()
    )

    logging.info("AllHandler completed")
