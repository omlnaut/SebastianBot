from datetime import datetime

from google.oauth2.credentials import Credentials

from sebastian.clients.google.task.client._models import TaskList, TaskResponse
from sebastian.clients.google.task.client.service_wrapper import TaskServiceWrapper
from sebastian.clients.google.task.client.taskslists import to_id
from sebastian.domain.shared import DateFilter
from sebastian.domain.task import Task, TaskLists

from .create_task_with_notes import build_task_body, post_create_task


class GoogleTaskClient:
    def __init__(self, credentials: Credentials, use_account_default: bool = False):
        self._service = TaskServiceWrapper(credentials)
        self._use_account_default = use_account_default

    def _fetch_tasklists(self) -> list[TaskList]:
        return self._service.get_tasklists()

    def _tasklist_id(self, tasklist: TaskLists) -> str:
        if self._use_account_default and tasklist == TaskLists.Default:
            return self._service.get_default_tasklist_id()
        return to_id(tasklist)

    def create_task_with_notes(
        self,
        tasklist: TaskLists,
        title: str,
        notes: str,
        due_date: datetime | None = None,
    ) -> Task:
        task_body = build_task_body(title, notes, due_date)
        parsed = post_create_task(self._service, self._tasklist_id(tasklist), task_body)
        return Task(
            id=parsed.id,
            title=parsed.title,
            due=parsed.due,
            notes=parsed.notes,
            tasklist=tasklist,
            link=parsed.webViewLink,
        )

    def get_tasks(
        self,
        tasklist: TaskLists = TaskLists.Default,
        include_completed: bool = False,
        due: DateFilter | None = None,
    ) -> list[Task]:
        def _response_to_domain(response: TaskResponse) -> Task:
            return Task(
                id=response.id,
                tasklist=tasklist,
                title=response.title,
                due=response.due,
                notes=response.notes,
                link=response.webViewLink,
            )

        tasks_response = self._service.get_tasks(
            self._tasklist_id(tasklist),
            include_completed=include_completed,
            due_min=due.start if due is not None else None,
            due_max=due.end if due is not None else None,
        )
        return [_response_to_domain(task) for task in tasks_response]

    def patch_task(
        self,
        # todo: TaskRef for identification
        tasklist: TaskLists,
        task_id: str,
        title: str | None = None,
        notes: str | None = None,
        due_date: datetime | None = None,
        completed: bool | None = None,
    ) -> None:
        """Setting a parameter None does not update the field"""
        self._service.patch_task(
            self._tasklist_id(tasklist),
            task_id,
            title=title,
            notes=notes,
            due_date=due_date,
            completed=completed,
        )

    def delete_task(self, tasklist: TaskLists, task_id: str) -> None:
        self._service.delete_task(self._tasklist_id(tasklist), task_id)
