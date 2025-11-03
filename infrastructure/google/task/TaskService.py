from typing import List, Optional
from datetime import datetime

from googleapiclient.discovery import build

from infrastructure.google.task.TaskModels import (
    TaskList,
    TaskResponse,
    CreatedTask,
    TaskListIds,
)
from shared.dates import get_end_of_day


class TaskService:
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = build(
            "tasks", "v1", credentials=credentials, cache_discovery=False
        )

    def fetch_tasklists(self) -> List[TaskList]:
        tasklists_response = self.service.tasklists().list().execute()
        items = tasklists_response.get("items", [])
        return [TaskList(**item) for item in items]

    def create_task_with_notes(
        self,
        tasklist_id: TaskListIds,
        title: str,
        notes: str,
        due_date: Optional[datetime] = None,
    ) -> CreatedTask:
        due_date = due_date or get_end_of_day()
        task_body = self._create_task_body(title, notes, due_date)
        created = (
            self.service.tasks()
            .insert(tasklist=tasklist_id.value, body=task_body)
            .execute()
        )
        parsed = TaskResponse(**created)
        return CreatedTask(
            title=parsed.title,
            due=parsed.due,
            notes=parsed.notes,
            tasklist=tasklist_id,
        )

    def _create_task_body(self, title: str, notes: str, due_date: datetime) -> dict:
        return {"title": title, "notes": notes, "due": due_date.isoformat()}
