from datetime import datetime
from typing import Self
from pydantic import BaseModel, Field

from cloud.functions.side_effects.create_task.models import CreateTaskEventGrid
from cloud.helper.event_grid import EventGridMixin
from cloud.functions.infrastructure.google.gmail.models import (
    ArchiveEmailEventGrid,
    PutEmailInToReadEventGrid,
)
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid

from sebastian.usecases.AllHandler.prompt_models import (
    AllHandlerEvent as ApplicationAllHandlerEvent,
)

import azure.functions as func


class AllHandlerEventGrid(EventGridMixin, BaseModel):
    create_task_events: list[CreateTaskEventGrid] = Field(
        default_factory=list, description="List of Tasks to be created"
    )
    archive_email_events: list[ArchiveEmailEventGrid] = Field(
        default_factory=list,
        description="Use this event if email does not need immediate action and will only be used for checking i.e. invoices in hindsight.",
    )
    put_email_in_to_read_events: list[PutEmailInToReadEventGrid] = Field(
        default_factory=list,
        description="Use this event to mark emails as to-read for later review, i.e. job offers, newsletters, etc.",
    )

    # todo: from_application for all event grids
    @classmethod
    def from_application(cls, application_event: ApplicationAllHandlerEvent) -> Self:
        create_task_events = [
            CreateTaskEventGrid(
                title=task.title,
                notes=task.notes,
                due=task.due,
                task_list_id=task.task_list_id,
            )
            for task in application_event.create_task_events
        ]
        archive_email_events = [
            ArchiveEmailEventGrid(title=email.title)
            for email in application_event.archive_email_events
        ]
        put_email_in_to_read_events = [
            PutEmailInToReadEventGrid(title=email.title)
            for email in application_event.put_email_in_to_read_events
        ]

        return cls(
            create_task_events=create_task_events,
            archive_email_events=archive_email_events,
            put_email_in_to_read_events=put_email_in_to_read_events,
        )
