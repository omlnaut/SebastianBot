from datetime import datetime
from pydantic import BaseModel, Field

from sebastian.protocols.google_task.models import TaskListIds


class CreateTaskEvent(BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds = TaskListIds.Default


class SendTelegramMessageEvent(BaseModel):
    message: str


class AllHandlerEvent(BaseModel):
    create_task_events: list[CreateTaskEvent] = Field(
        default_factory=list, description="List of Tasks to be created"
    )

    def is_empty(self) -> bool:
        return not bool(self.create_task_events)
