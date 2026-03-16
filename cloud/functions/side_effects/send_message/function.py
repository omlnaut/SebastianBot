import logging

import azure.functions as func

from cloud.dependencies import usecases
from .models import SendTelegramMessageEventGrid
from cloud.functions.side_effects.shared import (
    send_eventgrid_events,
    perform_usecase_from_eventgrid,
)
from function_app import app


@app.route(route="test_send_telegram_message")
def test_send_telegram_message(
    req: func.HttpRequest,
) -> func.HttpResponse:
    logging.info("Python event trigger function processed a request.")
    send_eventgrid_events([SendTelegramMessageEventGrid(message="hello there testi")])

    return func.HttpResponse("yay")


@app.event_grid_trigger(arg_name="azeventgrid")  # type: ignore
def send_telegram_message(azeventgrid: func.EventGridEvent):
    def create_request(
        event: SendTelegramMessageEventGrid,
    ) -> usecases.send_telegram_message.Request:
        return usecases.send_telegram_message.Request(message=event.message)

    perform_usecase_from_eventgrid(
        create_request,
        usecases.resolve_send_telegram_message,
        azeventgrid,
    )
