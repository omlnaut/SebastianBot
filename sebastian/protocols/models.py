from datetime import datetime

from pydantic import BaseModel, Field

from sebastian.protocols.google_task.models import TaskListIds


class CreateTask(BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds


class SendMessage(BaseModel):
    message: str


class AllActor(BaseModel):
    create_tasks: list[CreateTask] = Field(default_factory=list)
    send_messages: list[SendMessage] = Field(default_factory=list)
