from sebastian.protocols.google_task import TaskListIds


from pydantic import BaseModel

from cloud.helper.EventGridMixin import EventGridMixin


from sebastian.protocols.models import CompleteTask


class CompleteTaskEventGrid(EventGridMixin, BaseModel):
    tasklist_id: TaskListIds
    task_id: str

    @staticmethod
    def from_application(app_event: CompleteTask):
        return CompleteTaskEventGrid(
            tasklist_id=app_event.tasklist_id,
            task_id=app_event.task_id,
        )
