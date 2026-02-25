from sebastian.protocols.google_task import TaskListIds


from pydantic import BaseModel

from cloud.helper.EventGridMixin import EventGridMixin

from datetime import datetime

from sebastian.protocols.models import CreateTask, CompleteTask


class CreateTaskEventGrid(EventGridMixin, BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds = TaskListIds.Default

    @staticmethod
    def from_application(app_event: CreateTask):
        return CreateTaskEventGrid(
            title=app_event.title,
            notes=app_event.notes,
            due=app_event.due,
            task_list_id=app_event.task_list_id,
        )


class CompleteTaskEventGrid(EventGridMixin, BaseModel):
    tasklist_id: TaskListIds
    task_id: str

    @staticmethod
    def from_application(app_event: CompleteTask):
        return CompleteTaskEventGrid(
            tasklist_id=app_event.tasklist_id,
            task_id=app_event.task_id,
        )
