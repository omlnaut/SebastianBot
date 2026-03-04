from datetime import datetime

from sebastian.clients.google.task.client._models import TaskResponse
from sebastian.clients.google.task.client.taskslists import to_id
from sebastian.domain.task import TaskLists


def post_create_task(service, task_list: TaskLists, task_body: dict) -> TaskResponse:
    task_list_id = to_id(task_list)
    created = service.tasks().insert(tasklist=task_list_id, body=task_body).execute()
    return TaskResponse(**created)


def build_task_body(title: str, notes: str, due_date: datetime) -> dict:
    return {"title": title, "notes": notes, "due": due_date.isoformat()}
