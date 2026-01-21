from datetime import datetime
from pydantic import BaseModel, Field

from sebastian.protocols.google_task.models import TaskListIds


class CreateTaskEvent(BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds = TaskListIds.Default


class ArchiveEmailEvent(BaseModel):
    title: str = Field(
        ...,
        description="Title of the email to archive.",
    )


class PutEmailInToReadEvent(BaseModel):
    title: str = Field(
        ...,
        description="Title of the email to mark as to-read.",
    )


class SendTelegramMessageEvent(BaseModel):
    message: str


class AllHandlerEvent(BaseModel):
    archive_email_events: list[ArchiveEmailEvent] = Field(
        default_factory=list,
        description="Use this event if email does not need immediate action and will only be used for checking i.e. invoices in hindsight.",
    )
    put_email_in_to_read_events: list[PutEmailInToReadEvent] = Field(
        default_factory=list,
        description="Use this event to mark emails as to-read for later review, i.e. job offers, newsletters, etc.",
    )
    create_task_events: list[CreateTaskEvent] = Field(
        default_factory=list,
        description="Use this event when the email requires an action to be taken that is not covered by other the events.",
    )

    def is_empty(self) -> bool:
        return (
            not bool(self.create_task_events)
            and not bool(self.archive_email_events)
            and not bool(self.put_email_in_to_read_events)
        )
