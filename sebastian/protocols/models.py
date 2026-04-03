from datetime import datetime

from pydantic import BaseModel, Field

from sebastian.domain.gmail import GmailLabel
from sebastian.domain.task import TaskLists


class BaseActorEvent(BaseModel):
    pass


class CreateTask(BaseActorEvent):
    title: str = Field(min_length=1)
    tasklist: TaskLists
    notes: str | None = None
    due: datetime | None = None


class SendMessage(BaseActorEvent):
    message: str = Field(min_length=1)


class ModifyMailLabel(BaseActorEvent):
    email_id: str = Field(min_length=1)
    add_labels: list[GmailLabel] = Field(default_factory=list[GmailLabel])
    remove_labels: list[GmailLabel] = Field(default_factory=list[GmailLabel])


class CompleteTask(BaseActorEvent):
    tasklist: TaskLists
    task_id: str = Field(min_length=1)
