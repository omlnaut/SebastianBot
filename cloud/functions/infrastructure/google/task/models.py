from sebastian.protocols.google_task import TaskListIds


import azure.functions as func
from pydantic import BaseModel


import uuid
from datetime import datetime


class CreateTaskEvent(BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds = TaskListIds.Default
    subject: str = "create_task"

    def to_output(self) -> func.EventGridOutputEvent:
        data = self.model_dump(exclude=set("task_list_id"))
        data["task_list_id"] = self.task_list_id.value

        return func.EventGridOutputEvent(
            id=str(uuid.uuid4()),
            data=data,
            subject=self.subject,
            event_type="create_task_event",
            event_time=datetime.now(),
            data_version="1.0",
        )
