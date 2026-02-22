from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.protocols.google_task import (
    CreatedTask,
    TaskResponse,
    TaskList,
    TaskListIds,
)
from sebastian.shared.Result import Result

from .create_task_with_notes import build_task_body, post_create_task


class GoogleTaskClient:
    def __init__(self, credentials: Credentials):
        self._service = build(
            "tasks", "v1", credentials=credentials, cache_discovery=False
        )

    def fetch_tasklists(self) -> list[TaskList]:
        # todo parse with pydanctic
        tasklists_response = self._service.tasklists().list().execute()
        items = tasklists_response.get("items", [])
        return [TaskList(**item) for item in items]

    def create_task_with_notes(
        self, tasklist_id: TaskListIds, title: str, notes: str, due_date: datetime
    ) -> CreatedTask:
        task_body = build_task_body(title, notes, due_date)
        parsed = post_create_task(self._service, tasklist_id, task_body)
        return CreatedTask(
            title=parsed.title,
            due=parsed.due,
            notes=parsed.notes,
            tasklist=tasklist_id,
        )

    def get_tasks(
        self, tasklist_id: TaskListIds = TaskListIds.Default
    ) -> Result[list[TaskResponse]]:
        try:
            tasks_response = (
                self._service.tasks()
                .list(tasklist=tasklist_id.value, showCompleted=False)
                .execute()
            )
            items = tasks_response.get("items", [])
            tasks = [TaskResponse(**item) for item in items]
            return Result.from_item(item=tasks)
        except Exception as e:
            return Result.from_item(errors=[str(e)])

    def set_task_to_completed(
        self, tasklist_id: TaskListIds, task_id: str
    ) -> Result[None]:
        try:
            self._service.tasks().patch(
                tasklist=tasklist_id.value, task=task_id, body={"status": "completed"}
            ).execute()
            return Result.from_item(item=None)
        except Exception as e:
            return Result.from_item(errors=[str(e)])
