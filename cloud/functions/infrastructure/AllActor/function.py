import logging
from typing import Iterable
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from cloud.functions.infrastructure.google.gmail.helper import (
    modify_mail_label_output_binding,
)
from cloud.functions.infrastructure.google.task.helper import (
    task_output_binding,
    complete_task_output_binding,
)
from cloud.functions.infrastructure.telegram.helper import telegram_output_binding
from cloud.helper.event_grid import EventGridMixin
from cloud.helper.parsing import parse_payload
from function_app import app
import azure.functions as func


@app.event_grid_trigger(arg_name="azeventgrid")
@task_output_binding()
@complete_task_output_binding()
@telegram_output_binding()
@modify_mail_label_output_binding()
def all_actor_handler(
    azeventgrid: func.EventGridEvent,
    taskOutput: func.Out[func.EventGridOutputEvent],
    completeTaskOutput: func.Out[func.EventGridOutputEvent],
    telegramOutput: func.Out[func.EventGridOutputEvent],
    modifyMailLabelOutput: func.Out[func.EventGridOutputEvent],
):
    logging.info("AllActor event received")
    event = parse_payload(azeventgrid, AllActorEventGrid)

    _handle_events(event.create_tasks, taskOutput, "task creation")
    _handle_events(event.complete_tasks, completeTaskOutput, "task completion")
    _handle_events(event.send_messages, telegramOutput, "telegram message")
    _handle_events(event.modify_labels, modifyMailLabelOutput, "modify mail label")


def _handle_events(
    events: Iterable[EventGridMixin],
    output: func.Out[func.EventGridOutputEvent],
    event_type: str,
):
    event_outputs = [event.to_output() for event in events]
    if event_outputs:
        output.set(event_outputs)  # type: ignore
    logging.info(f"Emitting {len(event_outputs)} <{event_type}> events.")
