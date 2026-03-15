# pyright: basic
from sebastian.clients.google.task.client._models import TaskList, TaskResponse

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class TaskServiceWrapper:
    def __init__(self, credentials: Credentials):
        self._service = build(
            "tasks", "v1", credentials=credentials, cache_discovery=False
        )

    def create_task(self, tasklist_id: str, body: dict[str, str]) -> TaskResponse:
        created = (
            self._service.tasks().insert(tasklist=tasklist_id, body=body).execute()
        )
        return TaskResponse(**created)

    def get_tasks(self, tasklist_id: str) -> list[TaskResponse]:
        tasks = (
            self._service.tasks()
            .list(tasklist=tasklist_id, showCompleted=False)
            .execute()
        )
        return [TaskResponse(**task) for task in tasks.get("items", [])]

    def set_task_to_complete(self, tasklist_id: str, task_id: str) -> TaskResponse:
        updated = (
            self._service.tasks()
            .patch(tasklist=tasklist_id, task=task_id, body={"status": "completed"})
            .execute()
        )
        return TaskResponse(**updated)

    def get_tasklists(self) -> list[TaskList]:
        tasklists_response = self._service.tasklists().list().execute()
        items = tasklists_response.get("items", [])
        return [TaskList.model_validate(item) for item in items]
