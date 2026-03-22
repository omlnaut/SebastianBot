from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimeRange:
    from_date: datetime
    to_date: datetime


from pydantic import BaseModel, Field


class BookLendingInfo(BaseModel):
    title: str = Field(min_length=1)
    id: str = Field(min_length=9, max_length=9)
    location: str = Field(min_length=1)
    lending_timerange: TimeRange
