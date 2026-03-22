from typing import Protocol

from sebastian.domain.task import Task, TaskLists
from sebastian.shared.dates import TimeRange

from pydantic import BaseModel, Field

__all__ = ["BiboClient", "TaskClient"]


class BookLendingInfo(BaseModel):
    title: str = Field(min_length=1)
    id: str = Field(min_length=9, max_length=9)
    location: str = Field(min_length=1)
    lending_timerange: TimeRange


class BiboClient(Protocol):
    def fetch_open_lendings(self) -> list[BookLendingInfo]: ...


class TaskClient(Protocol):
    def get_tasks(self, tasklist: TaskLists) -> list[Task]: ...
