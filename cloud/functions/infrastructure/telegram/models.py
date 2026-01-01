import azure.functions as func
from pydantic import BaseModel


import datetime
import uuid


class SendTelegramMessageEvent(BaseModel):
    message: str

    def to_output(self) -> func.EventGridOutputEvent:
        return func.EventGridOutputEvent(
            id=str(uuid.uuid4()),
            data=self.model_dump(mode="json"),
            subject="send_telegram_message",
            event_type="send_telegram_message_event",
            event_time=datetime.datetime.now(),
            data_version="1.0",
        )
