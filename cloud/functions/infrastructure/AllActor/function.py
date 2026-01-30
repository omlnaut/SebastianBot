import logging
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from cloud.functions.infrastructure.google.task.helper import task_output_binding
from cloud.helper.parsing import parse_payload
from function_app import app
import azure.functions as func


@app.event_grid_trigger(arg_name="azeventgrid")
@task_output_binding()
async def all_actor_handler(
    azeventgrid: func.EventGridEvent,
    taskOutput: func.Out[func.EventGridOutputEvent],
):
    logging.info("AllActor event received")
    event = parse_payload(azeventgrid, AllActorEventGrid)

    task_events = [task_event.to_output() for task_event in event.create_tasks]
    taskOutput.set(task_events)  # type: ignore
    logging.info(
        f"Emitting {len(task_events)} task creation events: {[e.title for e in event.create_tasks]}"
    )
