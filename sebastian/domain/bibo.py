from enum import Enum

from pydantic import BaseModel, Field

from sebastian.domain.shared import TimeRange


class BiboAccounts(str, Enum):
    Oli = "oli"
    Katja = "katja"


class Lending(BaseModel):
    title: str = Field(min_length=1)
    id: str = Field(min_length=9, max_length=9)
    location: str = Field(min_length=1)
    lending_timerange: TimeRange
