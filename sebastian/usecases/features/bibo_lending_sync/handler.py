from dataclasses import dataclass
import logging

from sebastian.clients.google.task.client._models import TaskResponse
from sebastian.domain.task import TaskLists
from sebastian.protocols.models import AllActor, CompleteTask, CreateTask
from sebastian.usecases.usecase_handler import UseCaseHandler

from .protocols import BiboClient, BookLendingInfo, TaskClient

__all__ = ["Request", "Handler", "BiboClient", "TaskClient"]


@dataclass
class Request:
    pass


class Handler(UseCaseHandler[Request]):
    _tasklist = TaskLists.Bibo

    def __init__(self, bibo_client: BiboClient, task_client: TaskClient):
        self._bibo_client = bibo_client
        self._task_client = task_client

    def handle(self, request: Request) -> AllActor:
        lendings = self._bibo_client.fetch_open_lendings()
        tasks = self._task_client.get_tasks(self._tasklist)

        bibo_tasks = {
            book_id: task
            for task in tasks
            if (book_id := _extract_book_id(task)) is not None
        }
        lending_by_id = {lending.id: lending for lending in lendings}

        logging.info(
            f"BiboLendingSync: {len(lendings)} open lendings, "
            f"{len(bibo_tasks)} tracked bibo tasks"
        )

        creates: list[CreateTask] = []
        completes: list[CompleteTask] = []

        for lending in lendings:
            existing = bibo_tasks.get(lending.id)
            if existing is None:
                creates.append(_make_create_task(lending, self._tasklist))
            elif _due_date_differs(existing, lending):
                logging.info(
                    f"BiboLendingSync: due date changed for book_id={lending.id}, "
                    f"completing task {existing.id}"
                )
                completes.append(
                    CompleteTask(tasklist=self._tasklist, task_id=existing.id)
                )
                creates.append(_make_create_task(lending, self._tasklist))

        for book_id, task in bibo_tasks.items():
            if book_id not in lending_by_id:
                logging.info(
                    f"BiboLendingSync: lending for book_id={book_id} no longer open, "
                    f"completing task {task.id}"
                )
                completes.append(CompleteTask(tasklist=self._tasklist, task_id=task.id))

        logging.info(
            f"BiboLendingSync: creating {len(creates)} tasks, "
            f"completing {len(completes)} tasks"
        )
        return AllActor(create_tasks=creates, complete_tasks=completes)


def _extract_book_id(task: TaskResponse) -> str | None:
    if not task.notes:
        return None
    for line in task.notes.splitlines():
        if line.startswith("book_id: "):
            return line[len("book_id: ") :]
    return None


def _due_date_differs(task: TaskResponse, lending: BookLendingInfo) -> bool:
    if task.due is None:
        return True
    return task.due.date() != lending.lending_timerange.to_date.date()


def _make_create_task(lending: BookLendingInfo, tasklist: TaskLists) -> CreateTask:
    notes = (
        f"book_id: {lending.id}\n"
        f"title: {lending.title}\n"
        f"location: {lending.location}\n"
        f"from: {lending.lending_timerange.from_date.strftime('%Y-%m-%d')}\n"
        f"to: {lending.lending_timerange.to_date.strftime('%Y-%m-%d')}"
    )
    return CreateTask(
        title=f"Bibo: {lending.title}",
        tasklist=tasklist,
        notes=notes,
        due=lending.lending_timerange.to_date,
    )
