import logging
from dataclasses import dataclass
from typing import Sequence

from sebastian.domain.calendar import CalendarEvent, Calendars
from sebastian.protocols.models import (
    BaseActorEvent,
    CreateCalendarEvent,
    DeleteCalendarEvent,
    ModifyCalendarEvent,
)
from sebastian.domain.bibo import BiboAccounts
from sebastian.usecases.usecase_handler import UseCaseHandler

from .protocols import BiboClient, BookLendingInfo, CalendarClient

__all__ = ["Request", "Handler", "BiboAccounts", "BiboClient", "CalendarClient"]


@dataclass
class Request:
    pass


class Handler(UseCaseHandler[Request]):
    _calendar = Calendars.SharedPrimary

    def __init__(
        self,
        bibo_client: BiboClient,
        calendar_client: CalendarClient,
        account: BiboAccounts,
    ):
        self._bibo_client = bibo_client
        self._calendar_client = calendar_client
        self._sync_tag = f"BIBO_SYNC_{account.value.upper()}"

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        lendings = self._bibo_client.fetch_open_lendings()
        events = self._calendar_client.get_events(self._calendar, q=self._sync_tag)

        bibo_events = {
            book_id: event
            for event in events
            if (book_id := _extract_book_id(event.description)) is not None
        }
        lending_by_id = {lending.id: lending for lending in lendings}

        logging.info(
            f"BiboLendingSync: {len(lendings)} open lendings, "
            f"{len(bibo_events)} tracked bibo events"
        )

        creates: list[CreateCalendarEvent] = []
        modifies: list[ModifyCalendarEvent] = []
        deletes: list[DeleteCalendarEvent] = []

        for lending in lendings:
            existing = bibo_events.get(lending.id)
            if existing is None:
                creates.append(
                    _make_create_event(lending, self._calendar, self._sync_tag)
                )
            elif _date_differs(existing, lending):
                logging.info(
                    f"BiboLendingSync: date changed for book_id={lending.id}, "
                    f"modifying event {existing.id}"
                )
                modifies.append(
                    ModifyCalendarEvent(
                        calendar=self._calendar,
                        event_id=existing.id,
                        date=lending.lending_timerange.to_date.date(),
                    )
                )

        for book_id, event in bibo_events.items():
            if book_id not in lending_by_id:
                logging.info(
                    f"BiboLendingSync: lending for book_id={book_id} no longer open, "
                    f"deleting event {event.id}"
                )
                deletes.append(
                    DeleteCalendarEvent(calendar=self._calendar, event_id=event.id)
                )

        logging.info(
            f"BiboLendingSync: creating {len(creates)}, "
            f"modifying {len(modifies)}, deleting {len(deletes)} events"
        )
        return creates + modifies + deletes


def _extract_book_id(description: str | None) -> str | None:
    if not description:
        return None
    for line in description.splitlines():
        if line.startswith("book_id: "):
            return line[len("book_id: ") :]
    return None


def _date_differs(event: CalendarEvent, lending: BookLendingInfo) -> bool:
    return event.start.date() != lending.lending_timerange.to_date.date()


def _make_create_event(
    lending: BookLendingInfo, calendar: Calendars, sync_tag: str
) -> CreateCalendarEvent:
    description = (
        f"book_id: {lending.id}\n"
        f"title: {lending.title}\n"
        f"location: {lending.location}\n"
        f"from: {lending.lending_timerange.from_date.strftime('%Y-%m-%d')}\n"
        f"to: {lending.lending_timerange.to_date.strftime('%Y-%m-%d')}\n"
        f"{sync_tag}"
    )
    return CreateCalendarEvent(
        title=f"Bibo: {lending.title}",
        calendar=calendar,
        description=description,
        date=lending.lending_timerange.to_date.date(),
    )
