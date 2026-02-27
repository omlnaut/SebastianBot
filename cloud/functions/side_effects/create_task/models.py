from sebastian.protocols.google_task import TaskListIds

from cloud.helper.event_grid import EventGridModel

from datetime import datetime

from sebastian.protocols.models import CreateTask


class CreateTaskEventGrid(EventGridModel):
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
