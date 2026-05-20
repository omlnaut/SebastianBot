import logging
from dataclasses import dataclass
from typing import Sequence

from sebastian.domain.delivery_ready_task_note import DeliveryReadyTaskNote
from sebastian.domain.side_effect import SideEffect, CompleteTask, SendMessage
from sebastian.domain.task import Task, TaskLists
from sebastian.usecases.usecase_handler import UseCaseHandler

from .protocols import DhlClient, TaskClient

__all__ = ["Request", "Handler", "TaskClient", "DhlClient"]


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

    def handle(self, request: Request) -> Sequence[SideEffect]:
        tasks = self._fetch_open_tasks(request.tasklists)
        effects: list[SideEffect] = []
        delivery_ready_task_count = 0

        for task in tasks:
            note = DeliveryReadyTaskNote.from_text(task.notes)
            if not note.has_delivery_ready_tag:
                continue

            delivery_ready_task_count += 1
            if note.tracking_number is None:
                logging.info(
                    f"CheckParcelReceived: task_id={task.id} has no tracking number, skipping"
                )
                continue

            try:
                if self._dhl_client.is_retrieved(note.tracking_number):
                    effects.append(CompleteTask(tasklist=task.tasklist, task_id=task.id))
                    logging.info(
                        f"CheckParcelReceived: task_id={task.id} marked complete "
                        f"for tracking_number={note.tracking_number}"
                    )
            except Exception as exc:
                effects.append(
                    SendMessage(
                        message=(
                            "CheckParcelReceived: failed DHL check for "
                            f"task_id={task.id}, tracking_number={note.tracking_number}: {str(exc)}"
                        )
                    )
                )

        logging.info(
            f"CheckParcelReceived: {len(tasks)} open tasks, "
            f"{delivery_ready_task_count} tagged with delivery-ready contract"
        )
        return effects

    def _fetch_open_tasks(self, tasklists: tuple[TaskLists, ...]) -> list[Task]:
        tasks: list[Task] = []
        for tasklist in tasklists:
            tasks.extend(self._task_client.get_tasks(tasklist=tasklist))
        return tasks

