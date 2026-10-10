from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field

from sebastian.domain.calendar import Calendars
from sebastian.domain.gmail import GmailLabel, GmailLabels
from sebastian.domain.task import TaskLists


class SideEffect(BaseModel):
    pass


class CreateTask(SideEffect):
    title: str = Field(min_length=1)
    tasklist: TaskLists
    notes: str | None = None
    due: datetime | None = None


class CreateCalendarEvent(SideEffect):
    calendar: Calendars
    title: str = Field(min_length=1)
    date: date
    description: str | None = None


class SendMessage(SideEffect):
    message: str = Field(min_length=1)


class ModifyMailLabel(SideEffect):
    email_id: str = Field(min_length=1)
    add_labels: list[GmailLabel] = Field(default_factory=list[GmailLabel])
    remove_labels: list[GmailLabel] = Field(default_factory=list[GmailLabel])

    @classmethod
    def MarkAsRead(cls, email_id: str) -> "ModifyMailLabel":
        return cls(email_id=email_id, remove_labels=[GmailLabels.Unread])

    @classmethod
    def MarkAsUnread(cls, email_id: str) -> "ModifyMailLabel":
        return cls(email_id=email_id, add_labels=[GmailLabels.Unread])

    @classmethod
    def MarkAsProcessed(cls, email_id: str) -> "ModifyMailLabel":
        return cls(email_id=email_id, add_labels=[GmailLabels.Processed])


class PatchTask(SideEffect):
    tasklist: TaskLists
    task_id: str = Field(min_length=1)
    completed: bool | None = None
    due_date: date | None = None

    @classmethod
    def CompleteTask(cls, tasklist: TaskLists, task_id: str) -> Self:
        return cls(tasklist=tasklist, task_id=task_id, completed=True)

    @classmethod
    def SetDueDate(cls, tasklist: TaskLists, task_id: str, due_date: date) -> Self:
        return cls(tasklist=tasklist, task_id=task_id, due_date=due_date)


class DeleteCalendarEvent(SideEffect):
    calendar: Calendars
    event_id: str = Field(min_length=1)


class ModifyCalendarEvent(SideEffect):
    calendar: Calendars
    event_id: str = Field(min_length=1)
    date: date
