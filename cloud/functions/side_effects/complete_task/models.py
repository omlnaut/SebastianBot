from typing import Self, override

from cloud.helper.event_grid import EventGridModel
from sebastian.domain.task import TaskLists
from sebastian.domain.side_effect import PatchTask


class CompleteTaskEventGrid(EventGridModel[PatchTask]):
    tasklist: TaskLists
    task_id: str

    @classmethod
    @override
    def from_application(cls, app_event: PatchTask) -> Self:
        return cls(
            tasklist=app_event.tasklist,
            task_id=app_event.task_id,
        )
