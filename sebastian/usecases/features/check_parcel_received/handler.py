import logging
import re
from dataclasses import dataclass
from typing import Sequence

from sebastian.domain.side_effects import BaseActorEvent, CompleteTask, SendMessage
from sebastian.domain.task import Task, TaskLabels, TaskLists
from sebastian.usecases.usecase_handler import UseCaseHandler

from .protocols import DhlClient, TaskClient

__all__ = ["Request", "Handler", "TaskClient", "DhlClient"]

_TRACKING_PATTERN = re.compile(r"Tracking:\s*([A-Z0-9]+)", flags=re.IGNORECASE)


@dataclass
class Request:
    tasklists: tuple[TaskLists, ...] = (
        TaskLists.Default,
        TaskLists.Mangas,
        TaskLists.Bibo,
    )


class Handler(UseCaseHandler[Request]):
    def __init__(self, task_client: TaskClient, dhl_client: DhlClient):
        self._task_client = task_client
        self._dhl_client = dhl_client

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        tasks = self._fetch_open_tasks(request.tasklists)
        delivery_ready_tasks = [task for task in tasks if _is_delivery_ready_task(task)]
        logging.info(
            f"CheckParcelReceived: {len(tasks)} open tasks, "
            f"{len(delivery_ready_tasks)} tagged with {TaskLabels.DeliveryReady.value}"
        )

        effects: list[BaseActorEvent] = []

        for task in delivery_ready_tasks:
            tracking_id = _extract_tracking_id(task.notes)
            if tracking_id is None:
                logging.info(
                    f"CheckParcelReceived: task_id={task.id} has no tracking id, skipping"
                )
                continue

            try:
                if self._dhl_client.is_retrieved(tracking_id):
                    effects.append(
                        CompleteTask(tasklist=task.tasklist, task_id=task.id)
                    )
                    logging.info(
                        f"CheckParcelReceived: task_id={task.id} marked complete "
                        f"for tracking_id={tracking_id}"
                    )
            except Exception as exc:
                effects.append(
                    SendMessage(
                        message=(
                            "CheckParcelReceived: failed DHL check for "
                            f"task_id={task.id}, tracking_id={tracking_id}: {str(exc)}"
                        )
                    )
                )

        return effects

    def _fetch_open_tasks(self, tasklists: tuple[TaskLists, ...]) -> list[Task]:
        tasks: list[Task] = []
        for tasklist in tasklists:
            tasks.extend(self._task_client.get_tasks(tasklist=tasklist))
        return tasks


def _is_delivery_ready_task(task: Task) -> bool:
    return task.notes is not None and TaskLabels.DeliveryReady.value in task.notes


def _extract_tracking_id(notes: str | None) -> str | None:
    if notes is None:
        return None

    match = _TRACKING_PATTERN.search(notes)
    if match is None:
        return None

    return match.group(1).upper()
