import logging
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.infrastructure.google.task.models import (
    CreatedTask,
    TaskList,
    TaskListIds,
)
from sebastian.shared.dates import get_end_of_day

from .models import TaskResponse


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
        task_body = self._build_task_body(title, notes, due_date)
        parsed = self._post_create_task(tasklist_id, task_body)
        return CreatedTask(
            title=parsed.title,
            due=parsed.due,
            notes=parsed.notes,
            tasklist=tasklist_id,
        )

    def _post_create_task(
        self, tasklist_id: TaskListIds, task_body: dict
    ) -> TaskResponse:
        created = (
            self._service.tasks()
            .insert(tasklist=tasklist_id.value, body=task_body)
            .execute()
        )
        return TaskResponse(**created)

    def _build_task_body(self, title: str, notes: str, due_date: datetime) -> dict:
        return {"title": title, "notes": notes, "due": due_date.isoformat()}
