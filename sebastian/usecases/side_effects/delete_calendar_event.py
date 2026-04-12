from dataclasses import dataclass
from typing import Protocol, Sequence

from sebastian.domain.calendar import Calendars
from sebastian.protocols.models import BaseActorEvent
from sebastian.usecases.usecase_handler import UseCaseHandler


@dataclass
class Request:
    calendar: Calendars
    event_id: str


class CalendarEventClient(Protocol):
    def delete_event(self, calendar: Calendars, event_id: str) -> None: ...


class Handler(UseCaseHandler[Request]):
    def __init__(self, calendar_event_client: CalendarEventClient):
        self._client = calendar_event_client

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        self._client.delete_event(
            calendar=request.calendar,
            event_id=request.event_id,
        )
        return []
