from dataclasses import dataclass
from typing import Protocol

from sebastian.domain.task import TaskLists
from sebastian.protocols.models import AllActor
from sebastian.usecases.usecase_handler import UseCaseHandler


@dataclass
class Request:
    tasklist: TaskLists
    task_id: str


class TaskClient(Protocol):
    def set_task_to_completed(self, tasklist: TaskLists, task_id: str) -> None:
        """Should mark the given task as completed"""
        ...


class Handler(UseCaseHandler[Request]):
    def __init__(self, task_client: TaskClient):
        self._client = task_client

    def handle(self, request: Request) -> AllActor:
        self._client.set_task_to_completed(request.tasklist, request.task_id)
        return AllActor()
