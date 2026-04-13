from dataclasses import dataclass
from datetime import date
from typing import Protocol, Sequence

from sebastian.domain.calendar import Calendars
from sebastian.domain.side_effects import BaseActorEvent, SendMessage
from sebastian.usecases.usecase_handler import UseCaseHandler


@dataclass
class Request:
    calendar: Calendars
    title: str
    date: date
    description: str | None = None


class CalendarEventClient(Protocol):
    def create_event(
        self,
        calendar: Calendars,
        title: str,
        date: date,
        description: str | None = None,
    ) -> None: ...


class Handler(UseCaseHandler[Request]):
    def __init__(self, calendar_event_client: CalendarEventClient):
        self._client = calendar_event_client

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        self._client.create_event(
            calendar=request.calendar,
            title=request.title,
            date=request.date,
            description=request.description,
        )

        message = f"📅 CALENDAR EVENT created: {request.title} on {request.date.strftime('%d-%m-%Y')} in {request.calendar}"
        return [SendMessage(message=message)]
