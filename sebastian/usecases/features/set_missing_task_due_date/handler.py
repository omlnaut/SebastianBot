import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Sequence
from zoneinfo import ZoneInfo

from sebastian.domain.side_effect import PatchTask, SideEffect
from sebastian.domain.task import Task, TaskLists
from sebastian.usecases.usecase_handler import UseCaseHandler

from .protocols import TaskClient

__all__ = ["Request", "Handler", "TaskClient"]

_TIMEZONE = ZoneInfo("Europe/Berlin")


@dataclass
class Request:
    tasklists: tuple[TaskLists, ...] = (TaskLists.Default,)


class Handler(UseCaseHandler[Request]):
    def __init__(self, task_client: TaskClient):
        self._task_client = task_client

    def handle(self, request: Request) -> Sequence[SideEffect]:
        today = datetime.now(_TIMEZONE).date()
        effects: list[SideEffect] = []

        for tasklist in request.tasklists:
            effects.extend(self._handle_tasklist(tasklist, today))

        logging.info(
            f"SetMissingTaskDueDate: {len(effects)} tasks get due date {today}"
        )
        return effects

    def _handle_tasklist(self, tasklist: TaskLists, today: date) -> list[PatchTask]:
        effects: list[PatchTask] = []
        for task in self._task_client.get_tasks(tasklist=tasklist):
            if (effect := self._handle_task(task, today)) is not None:
                effects.append(effect)
        return effects

    def _handle_task(self, task: Task, today: date) -> PatchTask | None:
        if task.due is None:
            return PatchTask.SetDueDate(
                tasklist=task.tasklist, task_id=task.id, due_date=today
            )
        return None
