from typing import Self

from sebastian.protocols.google_task import TaskListIds


from cloud.helper.event_grid import EventGridModel


from sebastian.protocols.models import CompleteTask


class CompleteTaskEventGrid(EventGridModel):
    tasklist_id: TaskListIds
    task_id: str

    @classmethod
    def from_application(cls, app_event: CompleteTask) -> Self:
        return cls(
            tasklist_id=app_event.tasklist_id,
            task_id=app_event.task_id,
        )
