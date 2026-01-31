from datetime import datetime

from pydantic import BaseModel, Field

from sebastian.protocols.gmail import GmailLabel
from sebastian.protocols.google_task.models import TaskListIds


class CreateTask(BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds


class SendMessage(BaseModel):
    message: str


class ModifyMailLabel(BaseModel):
    email_id: str
    add_labels: list[GmailLabel] | None = None
    remove_labels: list[GmailLabel] | None = None


class AllActor(BaseModel):
    create_tasks: list[CreateTask] = Field(default_factory=list)
    send_messages: list[SendMessage] = Field(default_factory=list)
    modify_labels: list[ModifyMailLabel] = Field(default_factory=list)
