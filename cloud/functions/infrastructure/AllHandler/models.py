from datetime import datetime
from typing import Self
from pydantic import BaseModel, Field

from cloud.functions.infrastructure.google.task.models import CreateTaskEvent
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEvent

from sebastian.usecases.AllHandler.prompt_models import (
    AllHandlerEvent as ApplicationAllHandlerEvent,
)

import azure.functions as func


class AllHandlerEvent(BaseModel):
    create_task_events: list[CreateTaskEvent] = Field(
        default_factory=list, description="List of Tasks to be created"
    )

    def to_output(self) -> func.EventGridOutputEvent:
        return func.EventGridOutputEvent(
            id="allhandler-event",
            data=self.model_dump(mode="json"),
            subject="allhandler_event",
            event_type="allhandler_event",
            event_time=datetime.now(),
            data_version="1.0",
        )

    @classmethod
    def from_application(cls, application_event: ApplicationAllHandlerEvent) -> Self:
        create_task_events = [
            CreateTaskEvent(
                title=task.title,
                notes=task.notes,
                due=task.due,
                task_list_id=task.task_list_id,
            )
            for task in application_event.create_task_events
        ]

        return cls(create_task_events=create_task_events)
