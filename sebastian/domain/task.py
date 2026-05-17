from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum, auto

from pydantic import BaseModel, Field


class TaskLists(Enum):
    Default = auto()
    Mangas = auto()
    Bibo = auto()


class Task(BaseModel):
    id: str = Field(..., min_length=1)
    tasklist: TaskLists
    title: str = Field(..., min_length=1)
    due: datetime | None = None
    notes: str | None = None
    link: str | None = None


@dataclass(frozen=True)
class DateFilter:
    start: datetime | None = None
    end: datetime | None = None

    def __post_init__(self) -> None:
        if self.start is None and self.end is None:
            raise ValueError("At least one boundary must be set.")

        if self.start is not None and self.start.tzinfo is None:
            raise ValueError("start must be timezone-aware.")

        if self.end is not None and self.end.tzinfo is None:
            raise ValueError("end must be timezone-aware.")

        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("start must be before or equal to end.")

    @classmethod
    def on(cls, target_day: date) -> "DateFilter":
        start = datetime.combine(target_day, datetime.min.time(), tzinfo=timezone.utc)
        return cls(start=start, end=start + timedelta(days=1))

    @classmethod
    def range(
        cls, start: datetime | None = None, end: datetime | None = None
    ) -> "DateFilter":
        return cls(start=start, end=end)

    @classmethod
    def from_dates(
        cls, start: date | None = None, end: date | None = None
    ) -> "DateFilter":
        """Create DateFilter from date objects (UTC at start of day for start, end of day for end)."""
        start_dt = None
        if start is not None:
            start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)

        end_dt = None
        if end is not None:
            end_dt = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc)

        return cls(start=start_dt, end=end_dt)

    @classmethod
    def from_datetimes(
        cls, start: datetime | None = None, end: datetime | None = None
    ) -> "DateFilter":
        """Create DateFilter from datetime objects (must be timezone-aware)."""
        return cls(start=start, end=end)
