from pydantic import Field
from cloud.functions.infrastructure.google.gmail.models import ModifyMailLabelEventGrid

from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.functions.side_effects.create_task.models import (
    CompleteTaskEventGrid,
    CreateTaskEventGrid,
)
from cloud.helper.event_grid import EventGridModel
from sebastian.protocols.models import AllActor


class AllActorEventGrid(EventGridModel):
    create_tasks: list[CreateTaskEventGrid] = Field(default_factory=list)
    complete_tasks: list[CompleteTaskEventGrid] = Field(default_factory=list)
    send_messages: list[SendTelegramMessageEventGrid] = Field(default_factory=list)
    modify_labels: list[ModifyMailLabelEventGrid] = Field(default_factory=list)

    @staticmethod
    def from_application(app_event: AllActor):
        create_tasks = [
            CreateTaskEventGrid.from_application(task)
            for task in app_event.create_tasks
        ]
        complete_tasks = [
            CompleteTaskEventGrid.from_application(task)
            for task in app_event.complete_tasks
        ]
        send_messages = [
            SendTelegramMessageEventGrid.from_application(msg)
            for msg in app_event.send_messages
        ]
        # todo: from_application
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
            complete_tasks=complete_tasks,
            send_messages=send_messages,
            modify_labels=modify_labels,
        )
