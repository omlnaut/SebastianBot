from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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
    tasklist: TaskListIds
    due: datetime | None = None
    notes: str | None = None


class TaskResponse(BaseModel):
    kind: str
    id: str
    etag: str
    title: str
    due: datetime | None = None
    updated: datetime | None = None
    selfLink: str | None = None
    position: str | None = None
    notes: str | None = None
    status: str | None = None
    links: list[dict[str, str]] | None = None
    webViewLink: str | None = None
