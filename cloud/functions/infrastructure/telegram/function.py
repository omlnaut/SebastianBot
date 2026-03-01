import logging

import azure.functions as func

from cloud.dependencies.clients import resolve_telegram_client
from .models import SendTelegramMessageEventGrid
from cloud.functions.side_effects.shared import send_eventgrid_events
from cloud.helper import parse_payload
from function_app import app
from sebastian.infrastructure.telegram import service


@app.route(route="test_send_telegram_message")
def test_send_telegram_message(
    req: func.HttpRequest,
) -> func.HttpResponse:
    logging.info("Python event trigger function processed a request.")
    send_eventgrid_events([SendTelegramMessageEventGrid(message="hello there testi")])

    return func.HttpResponse("yay")


@app.event_grid_trigger(arg_name="azeventgrid")
async def send_telegram_message(azeventgrid: func.EventGridEvent):
    try:
        logging.info("Start to send telegram message")

        input_event = parse_payload(azeventgrid, SendTelegramMessageEventGrid)

        client = resolve_telegram_client()

        await service.send_telegram_message(client, input_event.message)

        logging.info(f"Telegram Message sent: {input_event.message}")
    except Exception as e:
        error_msg = f"Error sending telegram message: {str(e)}"
        logging.error(error_msg)
