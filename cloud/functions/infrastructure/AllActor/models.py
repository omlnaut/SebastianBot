from pydantic import BaseModel
from cloud.functions.infrastructure.google.task.models import CreateTaskEventGrid
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.helper.EventGridMixin import EventGridMixin


class AllActorEventGrid(EventGridMixin, BaseModel):
    create_tasks: list[CreateTaskEventGrid] = []
    send_messages: list[SendTelegramMessageEventGrid] = []
