from datetime import datetime
from typing import Self, override

from cloud.helper.event_grid import EventGridModel
from sebastian.domain.task import TaskLists
from sebastian.protocols.models import CreateTask


class CreateTaskEventGrid(EventGridModel[CreateTask]):
    title: str
    tasklist: TaskLists
    notes: str | None = None
    due: datetime | None = None

    @classmethod
    @override
    def from_application(cls, app_event: CreateTask) -> Self:
        return cls(
            title=app_event.title,
            notes=app_event.notes,
            due=app_event.due,
            tasklist=app_event.tasklist,
        )
