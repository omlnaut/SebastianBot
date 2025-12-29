from pydantic import BaseModel

from cloud.functions.infrastructure.google.task.models import CreateTaskEvent
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEvent


class AllHandlerEvent(BaseModel):
    create_task_events: list[CreateTaskEvent]
    send_telegram_message_events: list[SendTelegramMessageEvent]
