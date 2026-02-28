from itertools import groupby
import logging
import os
from typing import Callable, TypeVar, get_type_hints

from azure.eventgrid import EventGridPublisherClient
from azure.eventgrid import EventGridPublisherClient
import azure.functions as func
from azure.core.credentials import AzureKeyCredential


from cloud.functions.infrastructure.AllActor.helper import send_all_actor_events
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from cloud.helper.event_grid import EventGridInfo, EventGridModel
from sebastian.usecases.shared import UseCaseHandler


from cloud.functions.infrastructure.telegram.models import (
    SendTelegramMessageEventGrid,
)
from cloud.helper import parse_payload

TRequest = TypeVar("TRequest")
TEventModel = TypeVar("TEventModel", bound=EventGridModel)


def perform_usecase(
    create_request: Callable[[TEventModel], TRequest],
    resolve_handler: Callable[[], UseCaseHandler[TRequest]],
    az_event: func.EventGridEvent,
) -> None:

    def _extract_first_arg_type(func: Callable) -> type:
        hints = get_type_hints(func)
        for arg_name, arg_type in hints.items():
            if arg_name != "return":
                return arg_type
        raise ValueError(
            f"No argument type found in function {func.__name__} with hints {hints}"
        )

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


def send_eventgrid_events(events: list[EventGridModel]) -> None:
    def _load_eventgrid_info(env_name: str) -> EventGridInfo:
        raw_env_content = os.environ.get(env_name)
        assert (
            raw_env_content is not None
        ), f"Did not find environment variable: {env_name}"

        return EventGridInfo.model_validate_json(raw_env_content)

    for event_type, event_group in groupby(events, key=lambda x: type(x)):
        azure_events = [event.to_direct_output() for event in event_group]
        event_grid_info = _load_eventgrid_info(event_type.env_name())

        client = EventGridPublisherClient(
            endpoint=event_grid_info.uri,
            credential=AzureKeyCredential(event_grid_info.key),
        )
        client.send(azure_events)
