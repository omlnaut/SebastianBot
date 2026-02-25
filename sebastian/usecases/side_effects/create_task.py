from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol

from sebastian.protocols.google_task.models import CreatedTask, TaskListIds
from sebastian.shared import Result
from sebastian.shared.dates import get_end_of_day


@dataclass
class Request:
    tasklist_id: TaskListIds
    title: str
    notes: str
    due_date: Optional[datetime] = None


class TaskClient(Protocol):
    def create_task_with_notes(
        self,
        tasklist_id: TaskListIds,
        title: str,
        notes: str,
        due_date: datetime,
    ) -> CreatedTask:
        """Should create a task with notes"""
        ...


class Handler:
    def __init__(self, task_client: TaskClient):
        self._client = task_client

    def handle(self, request: Request) -> Result[CreatedTask]:
        due_date = request.due_date or get_end_of_day()
        try:
            created_task = self._client.create_task_with_notes(
                tasklist_id=request.tasklist_id,
                title=request.title,
                notes=request.notes,
                due_date=due_date,
            )
            return Result(item=created_task)
        except Exception as e:
            return Result(errors=[str(e)])
