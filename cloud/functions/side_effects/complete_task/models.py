from typing import Self, override


from cloud.helper.event_grid import EventGridModel


from sebastian.domain.task import TaskLists
from sebastian.protocols.models import CompleteTask


class CompleteTaskEventGrid(EventGridModel):
    tasklist: TaskLists
    task_id: str

    @classmethod
    @override
    def from_application(cls, app_event: CompleteTask) -> Self:
        return cls(
            tasklist=app_event.tasklist,
            task_id=app_event.task_id,
        )
