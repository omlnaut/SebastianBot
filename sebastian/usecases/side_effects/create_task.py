from dataclasses import dataclass
from datetime import datetime
from typing import Sequence, Optional, Protocol

from sebastian.domain.task import Task, TaskLists
from sebastian.protocols.models import BaseActorEvent
from sebastian.protocols.models import SendMessage
from sebastian.shared.dates import get_end_of_day
from sebastian.usecases.usecase_handler import UseCaseHandler


@dataclass
class Request:
    tasklist: TaskLists
    title: str
    notes: str
    due_date: Optional[datetime] = None


class TaskClient(Protocol):
    def create_task_with_notes(
        self,
        tasklist: TaskLists,
        title: str,
        notes: str,
        due_date: datetime,
    ) -> Task:
        """Should create a task with notes"""
        ...


class Handler(UseCaseHandler[Request]):
    def __init__(self, task_client: TaskClient):
        self._client = task_client

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        due_date = request.due_date or get_end_of_day()
        created_task = self._client.create_task_with_notes(
            tasklist=request.tasklist,
            title=request.title,
            notes=request.notes,
            due_date=due_date,
        )

        message = _build_message(created_task)
        return [SendMessage(message=message)]


def _build_message(created_task: Task) -> str:
    message = f"TASK created: {created_task.title}"
    if created_task.tasklist.name != TaskLists.Default.name:
        message += f" in {created_task.tasklist.name}"
    if created_task.due:
        message += f" ({created_task.due.date()})"
    if created_task.link:
        message += f"\n{created_task.link}"
    return message
