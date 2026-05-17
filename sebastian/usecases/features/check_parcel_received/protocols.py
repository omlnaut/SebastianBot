from typing import Protocol

from sebastian.domain.task import Task, TaskLists

__all__ = ["TaskClient", "DhlClient"]


class TaskClient(Protocol):
    def get_tasks(
        self,
        tasklist: TaskLists = TaskLists.Default,
        include_completed: bool = False,
    ) -> list[Task]: ...


class DhlClient(Protocol):
    def is_retrieved(self, tracking_number: str) -> bool: ...
