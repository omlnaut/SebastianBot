from datetime import datetime

from google.oauth2.credentials import Credentials

from sebastian.clients.google.task.client._models import TaskList, TaskResponse
from sebastian.clients.google.task.client.service_wrapper import TaskServiceWrapper
from sebastian.clients.google.task.client.taskslists import to_id

from sebastian.domain.task import Task, TaskLists

from .create_task_with_notes import build_task_body, post_create_task


class GoogleTaskClient:
    def __init__(self, credentials: Credentials):
        self._service = TaskServiceWrapper(credentials)

    def _fetch_tasklists(self) -> list[TaskList]:
        return self._service.get_tasklists()

    def create_task_with_notes(
        self, tasklist: TaskLists, title: str, notes: str, due_date: datetime
    ) -> Task:
        task_body = build_task_body(title, notes, due_date)
        parsed = post_create_task(self._service, tasklist, task_body)
        return Task(
            id=parsed.id,
            title=parsed.title,
            due=parsed.due,
            notes=parsed.notes,
            tasklist=tasklist,
            link=parsed.webViewLink,
        )

    def get_tasks(self, tasklist: TaskLists = TaskLists.Default) -> list[Task]:
        def _response_to_domain(response: TaskResponse) -> Task:
            return Task(
                id=response.id,
                tasklist=tasklist,
                title=response.title,
                due=response.due,
                notes=response.notes,
                link=response.webViewLink,
            )

        tasks_response = self._service.get_tasks(to_id(tasklist))
        return [_response_to_domain(task) for task in tasks_response]

    def set_task_to_completed(self, tasklist: TaskLists, task_id: str) -> None:
        self._service.set_task_to_complete(to_id(tasklist), task_id)
