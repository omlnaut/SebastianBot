from function_app import app
import datetime
import uuid
from typing import Optional

import azure.functions as func

from infrastructure.google.task.TaskSchemas import CreateTaskEvent


def task_output_binding(arg_name: str = "taskOutput"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="create_task",
        topic_endpoint_uri="CREATETASK_EVENT_GRID_URI",
        topic_key_setting="CREATETASK_EVENT_GRID_KEY",
    )


def create_task_output_event(
    event: CreateTaskEvent, subject: str = "create_task"
) -> func.EventGridOutputEvent:
    """Serialize a CreateTaskEvent into an EventGrid output event.

    Accepts a pydantic `CreateTaskEvent` and uses its dict as the `data` payload so
    pydantic handles datetime parsing/serialization.
    """
    data = event.model_dump(exclude=set("task_list_id"))
    data["task_list_id"] = event.task_list_id.value

    return func.EventGridOutputEvent(
        id=str(uuid.uuid4()),
        data=data,
        subject=subject,
        event_type="create_task_event",
        event_time=datetime.datetime.now(),
        data_version="1.0",
    )
