from datetime import datetime

from pydantic import BaseModel, Field

from sebastian.protocols.gmail import GmailLabel
from sebastian.protocols.google_task.models import TaskLists


class CreateTask(BaseModel):
    title: str = Field(min_length=1)
    tasklist: TaskLists
    notes: str | None = None
    due: datetime | None = None


class SendMessage(BaseModel):
    message: str = Field(min_length=1)


class ModifyMailLabel(BaseModel):
    email_id: str = Field(min_length=1)
    add_labels: list[GmailLabel] | None = None
    remove_labels: list[GmailLabel] | None = None


class CompleteTask(BaseModel):
    tasklist: TaskLists
    task_id: str = Field(min_length=1)


class AllActor(BaseModel):
    create_tasks: list[CreateTask] = Field(default_factory=list)
    complete_tasks: list[CompleteTask] = Field(default_factory=list)
    send_messages: list[SendMessage] = Field(default_factory=list)
    modify_labels: list[ModifyMailLabel] = Field(default_factory=list)
