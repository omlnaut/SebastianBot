from datetime import datetime
from typing import Optional

from sebastian.protocols.google_task import GoogleTaskClientProtocol
from sebastian.shared.dates import get_end_of_day

from .models import CreatedTask, TaskListIds


class TaskService:
    def __init__(self, client: GoogleTaskClientProtocol):
        self.client = client

    def create_task_with_notes(
        self,
        tasklist_id: TaskListIds,
        title: str,
        notes: str,
        due_date: Optional[datetime] = None,
    ) -> CreatedTask:
        due_date = due_date or get_end_of_day()
        return self.client.create_task_with_notes(
            tasklist_id=tasklist_id, title=title, notes=notes, due_date=due_date
        )
