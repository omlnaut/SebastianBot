from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.clients.google.task.client._models import TaskList, TaskResponse
from sebastian.clients.google.task.client.taskslists import to_id

from sebastian.domain.task import Task, TaskLists
from sebastian.shared.Result import Result

from .create_task_with_notes import build_task_body, post_create_task


class GoogleTaskClient:
    def __init__(self, credentials: Credentials):
        self._service = build(
            "tasks", "v1", credentials=credentials, cache_discovery=False
        )

    def _fetch_tasklists(self) -> list[TaskList]:
        tasklists_response = self._service.tasklists().list().execute()
        items = tasklists_response.get("items", [])
        return [TaskList.model_validate_json(item) for item in items]

    def create_task_with_notes(
        self, tasklist: TaskLists, title: str, notes: str, due_date: datetime
    ) -> Task:
        task_body = build_task_body(title, notes, due_date)
        parsed = post_create_task(self._service, tasklist, task_body)
        return Task(
            title=parsed.title,
            due=parsed.due,
            notes=parsed.notes,
            tasklist=tasklist,
            link=parsed.webViewLink,
        )

    def get_tasks(
        self, tasklist: TaskLists = TaskLists.Default
    ) -> Result[list[TaskResponse]]:
        try:
            tasks_response = (
                self._service.tasks()
                .list(tasklist=to_id(tasklist), showCompleted=False)
                .execute()
            )
            items = tasks_response.get("items", [])
            tasks = [TaskResponse(**item) for item in items]
            return Result.from_item(item=tasks)
        except Exception as e:
            return Result.from_item(errors=[str(e)])

    def set_task_to_completed(self, tasklist: TaskLists, task_id: str) -> Result[None]:
        try:
            self._service.tasks().patch(
                tasklist=to_id(tasklist), task=task_id, body={"status": "completed"}
            ).execute()
            # todo: error handling on non-existent task?
            return Result.from_item(item=None)
        except Exception as e:
            return Result.from_item(errors=[str(e)])
