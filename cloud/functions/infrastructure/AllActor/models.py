from typing import Self, override

from pydantic import Field

from cloud.functions.side_effects.complete_task.models import CompleteTaskEventGrid
from cloud.functions.side_effects.create_task.models import (
    CreateTaskEventGrid,
)
from cloud.functions.side_effects.modify_mail_label.models import (
    ModifyMailLabelEventGrid,
)
from cloud.functions.side_effects.send_message.models import (
    SendTelegramMessageEventGrid,
)
from cloud.helper.event_grid import EventGridModel
from sebastian.protocols.models import AllActor


class AllActorEventGrid(EventGridModel[AllActor]):
    create_tasks: list[CreateTaskEventGrid] = Field(
        default_factory=list[CreateTaskEventGrid]
    )
    complete_tasks: list[CompleteTaskEventGrid] = Field(
        default_factory=list[CompleteTaskEventGrid]
    )
    send_messages: list[SendTelegramMessageEventGrid] = Field(
        default_factory=list[SendTelegramMessageEventGrid]
    )
    modify_labels: list[ModifyMailLabelEventGrid] = Field(
        default_factory=list[ModifyMailLabelEventGrid]
    )

    @classmethod
    @override
    def from_application(cls, app_event: AllActor) -> Self:
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
        modify_labels = [
            ModifyMailLabelEventGrid.from_application(label)
            for label in app_event.modify_labels
        ]
        return cls(
            create_tasks=create_tasks,
            complete_tasks=complete_tasks,
            send_messages=send_messages,
            modify_labels=modify_labels,
        )
