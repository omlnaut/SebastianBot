import logging
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid

from cloud.functions.side_effects.shared import send_eventgrid_events
from cloud.helper.parsing import parse_payload
from function_app import app
import azure.functions as func


@app.event_grid_trigger(arg_name="azeventgrid")  # type: ignore
def all_actor_handler(
    azeventgrid: func.EventGridEvent,
):
    logging.info("AllActor event received")
    event = parse_payload(azeventgrid, AllActorEventGrid)
    logging.info(f"AllActor event parsed: {event}")
    send_eventgrid_events(event.create_tasks)
    send_eventgrid_events(event.complete_tasks)
    send_eventgrid_events(event.send_messages)
    send_eventgrid_events(event.modify_labels)
