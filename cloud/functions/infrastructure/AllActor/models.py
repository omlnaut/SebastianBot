from pydantic import BaseModel, Field
from cloud.functions.infrastructure.google.gmail.models import ModifyMailLabelEventGrid
from cloud.functions.infrastructure.google.task.models import CreateTaskEventGrid
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.helper.EventGridMixin import EventGridMixin
from sebastian.protocols.models import AllActor


class AllActorEventGrid(EventGridMixin, BaseModel):
    create_tasks: list[CreateTaskEventGrid] = Field(default_factory=list)
    send_messages: list[SendTelegramMessageEventGrid] = Field(default_factory=list)
    modify_labels: list[ModifyMailLabelEventGrid] = Field(default_factory=list)

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
        modify_labels = [
            ModifyMailLabelEventGrid(
                email_id=label.email_id,
                add_labels=label.add_labels,
                remove_labels=label.remove_labels,
            )
            for label in app_event.modify_labels
        ]
        return AllActorEventGrid(
            create_tasks=create_tasks,
            send_messages=send_messages,
            modify_labels=modify_labels,
        )
