import logging
import os
from itertools import groupby
from typing import Any, Callable, Sequence, TypeVar, get_type_hints

import azure.functions as func
from azure.core.credentials import AzureKeyCredential
from azure.eventgrid import EventGridPublisherClient

from cloud.functions.side_effects.complete_task.models import CompleteTaskEventGrid
from cloud.functions.side_effects.create_calendar_event.models import (
    CreateCalendarEventEventGrid,
)
from cloud.functions.side_effects.create_task.models import CreateTaskEventGrid
from cloud.functions.side_effects.modify_mail_label.models import (
    ModifyMailLabelEventGrid,
)
from cloud.functions.side_effects.send_message.models import (
    SendTelegramMessageEventGrid,
)
from cloud.helper import parse_payload
from cloud.helper.event_grid import EventGridInfo, EventGridModel
from sebastian.protocols.models import (
    BaseActorEvent,
    CompleteTask,
    CreateCalendarEvent,
    CreateTask,
    ModifyMailLabel,
    SendMessage,
)
from sebastian.usecases.usecase_handler import UseCaseHandler

EVENT_MAP: dict[type[BaseActorEvent], type[EventGridModel[Any]]] = {
    CompleteTask: CompleteTaskEventGrid,
    CreateCalendarEvent: CreateCalendarEventEventGrid,
    CreateTask: CreateTaskEventGrid,
    ModifyMailLabel: ModifyMailLabelEventGrid,
    SendMessage: SendTelegramMessageEventGrid,
}

TRequest = TypeVar("TRequest")


TEventModel = TypeVar("TEventModel", bound=EventGridModel[Any])


def perform_usecase_from_eventgrid(
    create_request: Callable[[TEventModel], TRequest],
    resolve_handler: Callable[[], UseCaseHandler[TRequest]],
    az_event: func.EventGridEvent,
) -> None:
    """
    Perform a usecase by creating a request from the EventGrid event,
    resolving the handler, and handling the request.
    """

    def _extract_first_arg_type(func: Callable[..., Any]) -> type[TEventModel]:
        hints = get_type_hints(func)
        for arg_name, arg_type in hints.items():
            if arg_name != "return":
                return arg_type
        raise ValueError(
            f"No argument type found in function {func.__name__} with hints {hints}"
        )

    event_model = _extract_first_arg_type(create_request)
    try:
        logging.info(f"EventGrid {event_model.base_name()} triggered")
        event = parse_payload(az_event, event_model)
        request = create_request(event)
        handler = resolve_handler()

        actor_result = handler.handle(request)

        events_to_send = [EVENT_MAP[type(e)].from_application(e) for e in actor_result]
        if events_to_send:
            send_eventgrid_events(events_to_send)

    except Exception as e:
        error_msg = f"Error {event_model.base_name()}: {str(e)}"
        logging.error(error_msg)
        logging.error(f"Error payload: {az_event.get_json()}")
        send_eventgrid_events([SendTelegramMessageEventGrid(message=error_msg)])

    logging.info(f"EventGrid {event_model.base_name()} completed")


def perform_usecase_from_request(
    request: TRequest, resolve_handler: Callable[[], UseCaseHandler[TRequest]]
) -> None:
    """
    Perform a usecase by resolving the handler and handling the request.
    """
    try:
        handler = resolve_handler()
        actor_result = handler.handle(request)
        events_to_send = [EVENT_MAP[type(e)].from_application(e) for e in actor_result]
        if events_to_send:
            send_eventgrid_events(events_to_send)
    except Exception as e:
        error_msg = f"Error performing usecase: {str(e)}"
        logging.error(error_msg)
        send_eventgrid_events([SendTelegramMessageEventGrid(message=error_msg)])


def send_eventgrid_events(events: Sequence[EventGridModel[Any]]) -> None:
    def _load_eventgrid_info(env_name: str) -> EventGridInfo:
        raw_env_content = os.environ.get(env_name)
        assert (
            raw_env_content is not None
        ), f"Did not find environment variable: {env_name}"

        return EventGridInfo.model_validate_json(raw_env_content)

    sorted_events = sorted(events, key=lambda x: type(x).__name__)
    for event_type, event_group_iterator in groupby(
        sorted_events, key=lambda x: type(x)
    ):
        event_group = list(event_group_iterator)
        logging.info(
            f"Sending {len(event_group)} EventGrid events for {event_type.env_name()}"
        )
        logging.info(event_group)
        azure_events = [event.to_direct_output() for event in event_group]
        event_grid_info = _load_eventgrid_info(event_type.env_name())

        client = EventGridPublisherClient(
            endpoint=event_grid_info.uri,
            credential=AzureKeyCredential(event_grid_info.key),
        )
        client.send(azure_events)  # type: ignore
