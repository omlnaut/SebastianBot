from datetime import datetime
import logging
import uuid
import azure.functions as func
from cloud.functions.infrastructure.AllHandler.helper import allhandler_output_binding
from cloud.functions.infrastructure.telegram.helper import telegram_output_binding
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEvent
from function_app import app


@app.route(route="test_trigger_allhandler")
@allhandler_output_binding()
def test_trigger_allhandler(
    req: func.HttpRequest, allHandlerOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("HTTP test - emit trigger all handler event")

    event = func.EventGridOutputEvent(
        id=str(uuid.uuid4()),
        data={"content": "Test AllHandler Trigger"},
        subject="trigger_all_handler",
        event_type="create_task_event",
        event_time=datetime.now(),
        data_version="1.0",
    )

    allHandlerOutput.set(event)

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
@telegram_output_binding()
def all_handler(
    azeventgrid: func.EventGridEvent,
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    logging.info("AllHandler triggered")

    telegramOutput.set(
        SendTelegramMessageEvent(message="AllHandler triggered").to_output()
    )

    logging.info("AllHandler completed")
