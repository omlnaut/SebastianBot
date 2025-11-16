from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.infrastructure.google.task.models import (
    CreatedTask,
    TaskList,
    TaskListIds,
)

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
