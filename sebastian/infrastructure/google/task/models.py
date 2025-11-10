from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class TaskList:
    kind: str
    id: str
    etag: str
    title: str
    updated: datetime | None = None
    selfLink: str | None = None


class TaskListIds(Enum):
    Default = "MDY0Mzc2NjgyMDc4MTc0Nzg3Mjk6MDow"
    Mangas = "WFRzM0JfdkdTXzl4WHVHNw"


@dataclass
class CreatedTask:
    title: str
    due: datetime
    notes: str | None
    tasklist: TaskListIds
