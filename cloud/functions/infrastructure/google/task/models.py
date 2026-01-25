from sebastian.protocols.google_task import TaskListIds


import azure.functions as func
from pydantic import BaseModel

from cloud.helper.event_grid_mixin import EventGridMixin

import uuid
from datetime import datetime


class CreateTaskEventGrid(EventGridMixin, BaseModel):
    title: str
    notes: str | None = None
    due: datetime | None = None
    task_list_id: TaskListIds = TaskListIds.Default
