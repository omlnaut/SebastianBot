from sebastian.protocols.google_task import TaskListIds


from pydantic import BaseModel

from cloud.helper.EventGridMixin import EventGridMixin

from datetime import datetime


class CreateTaskEventGrid(EventGridMixin, BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds = TaskListIds.Default
