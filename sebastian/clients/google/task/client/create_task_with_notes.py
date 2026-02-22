from datetime import datetime

from sebastian.protocols.google_task import TaskListIds
from sebastian.protocols.google_task.models import TaskResponse


def post_create_task(
    service, tasklist_id: TaskListIds, task_body: dict
) -> TaskResponse:
    created = (
        service.tasks().insert(tasklist=tasklist_id.value, body=task_body).execute()
    )
    return TaskResponse(**created)


def build_task_body(title: str, notes: str, due_date: datetime) -> dict:
    return {"title": title, "notes": notes, "due": due_date.isoformat()}
