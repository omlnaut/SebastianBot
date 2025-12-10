from datetime import datetime
from typing import Protocol

from sebastian.infrastructure.google.task.models import (
    CreatedTask,
    TaskList,
    TaskListIds,
)


class IGoogleTaskClient(Protocol):
    """Protocol for Google Task client operations."""

    def fetch_tasklists(self) -> list[TaskList]:
        """Fetch all task lists."""
        ...

    def create_task_with_notes(
        self, tasklist_id: TaskListIds, title: str, notes: str, due_date: datetime
    ) -> CreatedTask:
        """Create a task with notes in a specific task list."""
        ...
