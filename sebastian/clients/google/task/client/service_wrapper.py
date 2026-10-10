# pyright: basic
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.clients.google.task.client._models import TaskList, TaskResponse


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

    def get_tasks(
        self,
        tasklist_id: str,
        include_completed: bool = False,
        due_min: datetime | None = None,
        due_max: datetime | None = None,
    ) -> list[TaskResponse]:
        list_params: dict[str, str | bool] = {
            "tasklist": tasklist_id,
            "showCompleted": include_completed,
            "showHidden": include_completed,
        }

        if due_min is not None:
            list_params["dueMin"] = due_min.isoformat()
        if due_max is not None:
            list_params["dueMax"] = due_max.isoformat()

        tasks = self._service.tasks().list(**list_params).execute()
        return [TaskResponse(**task) for task in tasks.get("items", [])]

    def patch_task(
        self,
        tasklist_id: str,
        task_id: str,
        title: str | None = None,
        notes: str | None = None,
        due_date: datetime | None = None,
        completed: bool | None = None,
    ) -> TaskResponse:
        body: dict[str, str | None] = {}
        if title is not None:
            body["title"] = title
        if due_date is not None:
            body["due"] = due_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        if completed is not None:
            body["status"] = "completed" if completed else "needsAction"
        if notes is not None:
            body["notes"] = notes
        updated = (
            self._service.tasks()
            .patch(
                tasklist=tasklist_id,
                task=task_id,
                body={
                    **body,
                },
            )
            .execute()
        )
        return TaskResponse(**updated)

    def delete_task(self, tasklist_id: str, task_id: str) -> None:
        self._service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()

    def get_tasklists(self) -> list[TaskList]:
        tasklists_response = self._service.tasklists().list().execute()
        items = tasklists_response.get("items", [])
        return [TaskList.model_validate(item) for item in items]
