from datetime import datetime
from pydantic import BaseModel, Field

from cloud.functions.infrastructure.google.task.models import CreateTaskEvent
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEvent

import azure.functions as func


class AllHandlerEvent(BaseModel):
    create_task_events: list[CreateTaskEvent] = Field(
        default_factory=list, description="List of Tasks to be created"
    )
    send_telegram_message_events: list[SendTelegramMessageEvent] = Field(
        default_factory=list, description="List of Telegram messages to be sent"
    )

    def to_output(self) -> func.EventGridOutputEvent:
        return func.EventGridOutputEvent(
            id="allhandler-event",
            data=self.model_dump(),
            subject="allhandler_event",
            event_type="allhandler_event",
            event_time=datetime.now(),
            data_version="1.0",
        )
