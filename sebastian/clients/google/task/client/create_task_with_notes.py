from datetime import datetime

from sebastian.clients.google.task.client._models import TaskResponse
from sebastian.clients.google.task.client.service_wrapper import TaskServiceWrapper
from sebastian.clients.google.task.client.taskslists import to_id
from sebastian.domain.task import TaskLists


def post_create_task(
    service: TaskServiceWrapper, task_list: TaskLists, task_body: dict[str, str]
) -> TaskResponse:
    task_list_id = to_id(task_list)
    created = service.create_task(task_list_id, task_body)
    return created


def build_task_body(title: str, notes: str, due_date: datetime) -> dict[str, str]:
    return {"title": title, "notes": notes, "due": due_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")}
