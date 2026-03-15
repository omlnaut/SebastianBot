from datetime import datetime

from pydantic import BaseModel, Field

from sebastian.domain.gmail import GmailLabel
from sebastian.domain.task import TaskLists


class CreateTask(BaseModel):
    title: str = Field(min_length=1)
    tasklist: TaskLists
    notes: str | None = None
    due: datetime | None = None


class SendMessage(BaseModel):
    message: str = Field(min_length=1)


class ModifyMailLabel(BaseModel):
    email_id: str = Field(min_length=1)
    add_labels: list[GmailLabel] = Field(default_factory=list[GmailLabel])
    remove_labels: list[GmailLabel] = Field(default_factory=list[GmailLabel])


class CompleteTask(BaseModel):
    tasklist: TaskLists
    task_id: str = Field(min_length=1)


class AllActor(BaseModel):
    create_tasks: list[CreateTask] = Field(default_factory=list[CreateTask])
    complete_tasks: list[CompleteTask] = Field(default_factory=list[CompleteTask])
    send_messages: list[SendMessage] = Field(default_factory=list[SendMessage])
    modify_labels: list[ModifyMailLabel] = Field(default_factory=list[ModifyMailLabel])
