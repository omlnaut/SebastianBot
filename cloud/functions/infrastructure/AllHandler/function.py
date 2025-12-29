import logging
import azure.functions as func
from cloud.functions.infrastructure.telegram.helper import telegram_output_binding
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEvent
from function_app import app


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
