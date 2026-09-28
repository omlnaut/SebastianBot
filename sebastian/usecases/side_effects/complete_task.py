from dataclasses import dataclass
from typing import Protocol, Sequence

from sebastian.domain.task import TaskLists
from sebastian.domain.side_effect import SideEffect
from sebastian.usecases.usecase_handler import UseCaseHandler


@dataclass
class Request:
    tasklist: TaskLists
    task_id: str


class TaskClient(Protocol):
    def patch_task(
        self, tasklist: TaskLists, task_id: str, *, completed: bool | None = None
    ) -> None: ...


class Handler(UseCaseHandler[Request]):
    def __init__(self, task_client: TaskClient):
        self._client = task_client

    def handle(self, request: Request) -> Sequence[SideEffect]:
        self._client.patch_task(request.tasklist, request.task_id, completed=True)
        return []
