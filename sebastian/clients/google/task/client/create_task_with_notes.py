from datetime import datetime

from sebastian.clients.google.task.models import TaskResponse
from sebastian.protocols.google_task import TaskListIds


def post_create_task(
    service, tasklist_id: TaskListIds, task_body: dict
) -> TaskResponse:
    created = (
        service.tasks().insert(tasklist=tasklist_id.value, body=task_body).execute()
    )
    return TaskResponse(**created)


def build_task_body(title: str, notes: str, due_date: datetime) -> dict:
    return {"title": title, "notes": notes, "due": due_date.isoformat()}
