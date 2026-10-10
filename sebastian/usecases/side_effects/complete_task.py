from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol, Sequence

from sebastian.domain.task import TaskLists
from sebastian.domain.side_effect import SideEffect
from sebastian.usecases.usecase_handler import UseCaseHandler


@dataclass
class Request:
    tasklist: TaskLists
    task_id: str
    completed: bool | None = True
    due_date: date | None = None


class TaskClient(Protocol):
    def patch_task(
        self,
        tasklist: TaskLists,
        task_id: str,
        *,
        completed: bool | None = None,
        due_date: datetime | None = None,
    ) -> None: ...


class Handler(UseCaseHandler[Request]):
    def __init__(self, task_client: TaskClient):
        self._client = task_client

    def handle(self, request: Request) -> Sequence[SideEffect]:
        due = (
            datetime(
                request.due_date.year,
                request.due_date.month,
                request.due_date.day,
                tzinfo=timezone.utc,
            )
            if request.due_date
            else None
        )
        self._client.patch_task(
            request.tasklist,
            request.task_id,
            completed=request.completed,
            due_date=due,
        )
        return []
