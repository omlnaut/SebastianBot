from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from infrastructure.google.task.TaskModels import TaskListIds


class CreateTaskEvent(BaseModel):
    title: str
    notes: Optional[str] = None
    due: Optional[datetime] = None
    task_list_id: TaskListIds = TaskListIds.Default
