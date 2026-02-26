import logging
from typing import Callable, TypeVar

import azure.functions as func


from cloud.functions.infrastructure.AllActor.helper import send_all_actor_events
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from sebastian.usecases.shared import UseCaseHandler


from cloud.functions.infrastructure.telegram.models import (
    SendTelegramMessageEventGrid,
)
from cloud.helper import event_grid, parse_payload

TRequest = TypeVar("TRequest")
TEventModel = TypeVar("TEventModel", bound=event_grid.EventGridModel)


def perform_usecase(
    event_model: type[TEventModel],
    create_request: Callable[[TEventModel], TRequest],
    resolve_handler: Callable[[], UseCaseHandler[TRequest]],
    az_event: func.EventGridEvent,
) -> None:
    try:
        logging.info(f"EventGrid {event_model.base_name} triggered")
        event = parse_payload(az_event, event_model)
        request = create_request(event)
        handler = resolve_handler()

        actor_result = handler.handle(request)

        send_all_actor_events([AllActorEventGrid.from_application(actor_result)])

    except Exception as e:
        error_msg = f"Error {event_model.base_name}: {str(e)}"
        logging.error(error_msg)
        send_all_actor_events(
            [
                AllActorEventGrid(
                    send_messages=[SendTelegramMessageEventGrid(message=error_msg)]
                )
            ]
        )

    logging.info(f"EventGrid {event_model.base_name} completed")
