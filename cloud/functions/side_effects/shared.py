import logging
from typing import Callable, TypeVar, get_type_hints

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
    create_request: Callable[[TEventModel], TRequest],
    resolve_handler: Callable[[], UseCaseHandler[TRequest]],
    az_event: func.EventGridEvent,
) -> None:
    event_model = _extract_first_arg_type(create_request)
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


def _extract_first_arg_type(func: Callable) -> type:
    hints = get_type_hints(func)
    for arg_name, arg_type in hints.items():
        if arg_name != "return":
            return arg_type
    raise ValueError(
        f"No argument type found in function {func.__name__} with hints {hints}"
    )
