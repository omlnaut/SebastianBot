from datetime import datetime
from enum import Enum, auto

from pydantic import BaseModel, Field


class TaskLists(Enum):
    Default = auto()
    Mangas = auto()
    Bibo = auto()


class Task(BaseModel):
    tasklist: TaskLists
    title: str = Field(..., min_length=1)
    due: datetime | None = None
    notes: str | None = None
    link: str | None = None
