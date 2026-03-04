from dataclasses import dataclass
from typing import Protocol

from sebastian.domain.task import TaskLists
from sebastian.protocols.models import AllActor, SendMessage
from sebastian.shared import Result


@dataclass
class Request:
    tasklist: TaskLists
    task_id: str


class TaskClient(Protocol):
    def set_task_to_completed(self, tasklist: TaskLists, task_id: str) -> Result[None]:
        """Should mark the given task as completed"""
        ...


class Handler:
    def __init__(self, task_client: TaskClient):
        self._client = task_client

    def handle(self, request: Request) -> AllActor:
        result = self._client.set_task_to_completed(request.tasklist, request.task_id)
        if result.has_errors():
            return AllActor(send_messages=[SendMessage(message=result.errors_string)])

        return AllActor()
