import os

from azure.eventgrid import EventGridPublisherClient
from azure.core.credentials import AzureKeyCredential

from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from function_app import app


def all_actor_output_binding(arg_name: str = "allActorOutput"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="AllActorEvent",
        topic_endpoint_uri="ALLACTOR_EVENT_GRID_URI",
        topic_key_setting="ALLACTOR_EVENT_GRID_KEY",
    )


def send_all_actor_events(events: list[AllActorEventGrid]):
    client = EventGridPublisherClient(
        endpoint=os.environ["ALLACTOR_EVENT_GRID_URI"],
        credential=AzureKeyCredential(os.environ["ALLACTOR_EVENT_GRID_KEY"]),
    )
    azure_events = [event.to_direct_output() for event in events]
    client.send(azure_events)
