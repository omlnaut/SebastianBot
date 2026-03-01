from typing import Self

from sebastian.protocols.google_task import TaskListIds

from cloud.helper.event_grid import EventGridModel

from datetime import datetime

from sebastian.protocols.models import CreateTask


class CreateTaskEventGrid(EventGridModel[CreateTask]):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds = TaskListIds.Default

    @classmethod
    def from_application(cls, app_event: CreateTask) -> Self:
        return cls(
            title=app_event.title,
            notes=app_event.notes,
            due=app_event.due,
            task_list_id=app_event.task_list_id,
        )

    def to_application(self) -> CreateTask:
        return CreateTask(
            title=self.title,
            notes=self.notes,
            due=self.due,
            task_list_id=self.task_list_id,
        )
