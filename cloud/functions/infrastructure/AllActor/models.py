from pydantic import BaseModel, Field
from cloud.functions.infrastructure.google.task.models import CreateTaskEventGrid
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.helper.EventGridMixin import EventGridMixin
from sebastian.protocols.models import AllActor


class AllActorEventGrid(EventGridMixin, BaseModel):
    create_tasks: list[CreateTaskEventGrid] = Field(default_factory=list)
    send_messages: list[SendTelegramMessageEventGrid] = Field(default_factory=list)

    @staticmethod
    def from_application(app_event: AllActor):
        create_tasks = [
            CreateTaskEventGrid.from_application(task)
            for task in app_event.create_tasks
        ]
        send_messages = [
            SendTelegramMessageEventGrid.from_application(msg)
            for msg in app_event.send_messages
        ]
        return AllActorEventGrid(
            create_tasks=create_tasks,
            send_messages=send_messages,
        )
