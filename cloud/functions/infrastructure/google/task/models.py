from sebastian.protocols.google_task import TaskListIds


import azure.functions as func
from pydantic import BaseModel, field_serializer


import uuid
from datetime import datetime


class CreateTaskEvent(BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds = TaskListIds.Default
    subject: str = "create_task"

    @field_serializer("task_list_id")
    def serialize_task_list_id(self, v: TaskListIds) -> str:
        return v.value

    def to_output(self) -> func.EventGridOutputEvent:
        return func.EventGridOutputEvent(
            id=str(uuid.uuid4()),
            data=self.model_dump(),
            subject=self.subject,
            event_type="create_task_event",
            event_time=datetime.now(),
            data_version="1.0",
        )
