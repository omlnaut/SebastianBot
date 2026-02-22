from datetime import datetime
from typing import Protocol

from sebastian.shared.Result import Result

from .models import (
    CreatedTask,
    TaskResponse,
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

    def get_tasks(self, tasklist_id: TaskListIds) -> Result[list[TaskResponse]]:
        """Fetch all currently open tasks from a specific task list."""
        ...

    def set_task_to_completed(
        self, tasklist_id: TaskListIds, task_id: str
    ) -> Result[None]:
        """Mark a specific task as completed."""
        ...
