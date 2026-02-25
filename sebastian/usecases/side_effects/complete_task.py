from dataclasses import dataclass
from typing import Protocol

from sebastian.protocols.google_task.models import TaskListIds
from sebastian.shared import Result


@dataclass
class Request:
    tasklist_id: TaskListIds
    task_id: str


class TaskClient(Protocol):
    def set_task_to_completed(
        self, tasklist_id: TaskListIds, task_id: str
    ) -> Result[None]:
        """Should mark the given task as completed"""
        ...


class Handler:
    def __init__(self, task_client: TaskClient):
        self._client = task_client

    def handle(self, request: Request) -> Result[None]:
        return self._client.set_task_to_completed(request.tasklist_id, request.task_id)
