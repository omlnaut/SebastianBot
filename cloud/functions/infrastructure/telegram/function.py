import logging

import azure.functions as func

from cloud.dependencies.clients import resolve_telegram_client
from .SendTelegramMessageEvent import SendTelegramMessageEvent
from cloud.helper import parse_payload
from function_app import app
from sebastian.infrastructure.telegram import service

from .helper import telegram_output_binding


@app.route(route="test_send_telegram_message")
@telegram_output_binding()
def test_send_telegram_message(
    req: func.HttpRequest, telegramOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("Python event trigger function processed a request.")
    telegramOutput.set(
        SendTelegramMessageEvent(message="hello there testi").to_output()
    )

    return func.HttpResponse("yay")


@app.event_grid_trigger(arg_name="azeventgrid")
async def send_telegram_message(azeventgrid: func.EventGridEvent):
    try:
        logging.info("Start to send telegram message")

        input_event = parse_payload(azeventgrid, SendTelegramMessageEvent)

        client = resolve_telegram_client()

        await service.send_telegram_message(client, input_event.message)

        logging.info(f"Telegram Message sent: {input_event.message}")
    except Exception as e:
        error_msg = f"Error sending telegram message: {str(e)}"
        logging.error(error_msg)
