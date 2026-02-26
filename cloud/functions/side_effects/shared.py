import logging
from typing import Callable, TypeVar

import azure.functions as func

from pydantic import BaseModel

from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from sebastian.usecases.shared import UseCaseHandler

from cloud.functions.infrastructure.telegram.models import (
    SendTelegramMessageEventGrid,
)
from cloud.helper import parse_payload

TRequest = TypeVar("TRequest")
TEventModel = TypeVar("TEventModel", bound=BaseModel)


def perform_usecase(
    event_model: type[TEventModel],
    create_request: Callable[[TEventModel], TRequest],
    resolve_handler: Callable[[], UseCaseHandler[TRequest]],
    az_event: func.EventGridEvent,
):
    try:
        logging.info("EventGrid complete task triggered")
        event = parse_payload(az_event, event_model)
        request = create_request(event)
        handler = resolve_handler()

        actor_result = handler.handle(request)

        return AllActorEventGrid.from_application(actor_result).to_output()

    except Exception as e:
        error_msg = f"Error completing task: {str(e)}"
        logging.error(error_msg)
        return AllActorEventGrid(
            send_messages=[SendTelegramMessageEventGrid(message=error_msg)]
        ).to_output()
