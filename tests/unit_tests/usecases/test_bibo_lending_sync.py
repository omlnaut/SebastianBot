from datetime import date, datetime, timezone
from typing import Sequence

from sebastian.domain.calendar import CalendarEvent, Calendars
from sebastian.protocols.models import (
    BaseActorEvent,
    CreateCalendarEvent,
    DeleteCalendarEvent,
    ModifyCalendarEvent,
)
from sebastian.shared.dates import TimeRange
from sebastian.usecases.features.bibo_lending_sync.handler import Handler, Request
from sebastian.usecases.features.bibo_lending_sync.protocols import BookLendingInfo

_CALENDAR = Calendars.SharedPrimary


def _make_lending(
    book_id: str = "123456789",
    title: str = "Some Book",
    location: str = "Shelf A",
    from_date: datetime = datetime(2026, 3, 1, tzinfo=timezone.utc),
    to_date: datetime = datetime(2026, 4, 1, tzinfo=timezone.utc),
) -> BookLendingInfo:
    return BookLendingInfo(
        title=title,
        id=book_id,
        location=location,
        lending_timerange=TimeRange(from_date=from_date, to_date=to_date),
    )


def _make_event(
    book_id: str | None = "123456789",
    start: datetime = datetime(2026, 4, 1, tzinfo=timezone.utc),
    event_id: str = "event-1",
) -> CalendarEvent:
    description = (
        f"book_id: {book_id}\ntitle: Some Book\nBIBO_SYNC" if book_id else None
    )
    end = start
    return CalendarEvent(
        id=event_id,
        title="Bibo: Some Book",
        description=description,
        start=start,
        end=end,
    )


class _FakeBiboClient:
    def __init__(self, lendings: list[BookLendingInfo]):
        self._lendings = lendings

    def fetch_open_lendings(self) -> list[BookLendingInfo]:
        return self._lendings


class _FakeCalendarClient:
    def __init__(self, events: list[CalendarEvent]):
        self._events = events

    def get_events(
        self,
        calendar: Calendars,
        time_min: date | None = None,
        time_max: date | None = None,
        q: str | None = None,
    ) -> list[CalendarEvent]:
        return self._events


def _run(
    lendings: list[BookLendingInfo], events: list[CalendarEvent]
) -> Sequence[BaseActorEvent]:
    handler = Handler(
        bibo_client=_FakeBiboClient(lendings),
        calendar_client=_FakeCalendarClient(events),
    )
    return handler.handle(Request())


def test_new_lending_creates_event():
    lending = _make_lending()

    result = _run(lendings=[lending], events=[])

    assert len([e for e in result if isinstance(e, CreateCalendarEvent)]) == 1
    assert len([e for e in result if isinstance(e, DeleteCalendarEvent)]) == 0
    event = [e for e in result if isinstance(e, CreateCalendarEvent)][0]
    assert event.title == "Bibo: Some Book"
    assert event.calendar == _CALENDAR
    assert event.date == lending.lending_timerange.to_date.date()
    assert event.description is not None
    assert "book_id: 123456789" in event.description


def test_new_lending_description_contains_all_fields():
    lending = _make_lending(
        book_id="987654321",
        title="Another Book",
        location="Floor 2",
        from_date=datetime(2026, 3, 5, tzinfo=timezone.utc),
        to_date=datetime(2026, 4, 10, tzinfo=timezone.utc),
    )

    result = _run(lendings=[lending], events=[])

    description = [e for e in result if isinstance(e, CreateCalendarEvent)][
        0
    ].description
    assert description is not None
    assert "book_id: 987654321" in description
    assert "title: Another Book" in description
    assert "location: Floor 2" in description
    assert "from: 2026-03-05" in description
    assert "to: 2026-04-10" in description
    assert "BIBO_SYNC" in description


def test_existing_event_same_date_no_action():
    due = datetime(2026, 4, 1, tzinfo=timezone.utc)
    lending = _make_lending(to_date=due)
    event = _make_event(start=due)

    result = _run(lendings=[lending], events=[event])

    assert [e for e in result if isinstance(e, CreateCalendarEvent)] == []
    assert [e for e in result if isinstance(e, ModifyCalendarEvent)] == []
    assert [e for e in result if isinstance(e, DeleteCalendarEvent)] == []


def test_date_changed_emits_modify_event():
    old_due = datetime(2026, 3, 20, tzinfo=timezone.utc)
    new_due = datetime(2026, 4, 5, tzinfo=timezone.utc)
    lending = _make_lending(to_date=new_due)
    event = _make_event(start=old_due, event_id="event-old")

    result = _run(lendings=[lending], events=[event])

    assert [e for e in result if isinstance(e, CreateCalendarEvent)] == []
    assert [e for e in result if isinstance(e, DeleteCalendarEvent)] == []
    assert len([e for e in result if isinstance(e, ModifyCalendarEvent)]) == 1
    modify = [e for e in result if isinstance(e, ModifyCalendarEvent)][0]
    assert modify.calendar == _CALENDAR
    assert modify.event_id == "event-old"
    assert modify.date == new_due.date()


def test_returned_book_event_is_deleted():
    event = _make_event(event_id="event-returned", book_id="123456789")

    result = _run(lendings=[], events=[event])

    assert len([e for e in result if isinstance(e, DeleteCalendarEvent)]) == 1
    assert [e for e in result if isinstance(e, DeleteCalendarEvent)][
        0
    ] == DeleteCalendarEvent(calendar=_CALENDAR, event_id="event-returned")
    assert [e for e in result if isinstance(e, CreateCalendarEvent)] == []


def test_event_without_book_id_is_ignored():
    event = _make_event(event_id="event-noid", book_id=None)

    result = _run(lendings=[], events=[event])

    assert [e for e in result if isinstance(e, DeleteCalendarEvent)] == []
    assert [e for e in result if isinstance(e, CreateCalendarEvent)] == []


def test_no_lendings_no_events_returns_empty():
    result = _run(lendings=[], events=[])

    assert result == []


def test_mixed_scenario():
    unchanged_due = datetime(2026, 4, 1, tzinfo=timezone.utc)
    changed_old_due = datetime(2026, 3, 10, tzinfo=timezone.utc)
    changed_new_due = datetime(2026, 4, 15, tzinfo=timezone.utc)

    lending_new = _make_lending(book_id="111111111", title="New Book")
    lending_unchanged = _make_lending(
        book_id="222222222", title="Unchanged Book", to_date=unchanged_due
    )
    lending_changed = _make_lending(
        book_id="333333333", title="Changed Book", to_date=changed_new_due
    )

    event_unchanged = _make_event(
        event_id="event-unchanged", book_id="222222222", start=unchanged_due
    )
    event_changed = _make_event(
        event_id="event-changed", book_id="333333333", start=changed_old_due
    )
    event_returned = _make_event(
        event_id="event-returned", book_id="444444444", start=unchanged_due
    )

    result = _run(
        lendings=[lending_new, lending_unchanged, lending_changed],
        events=[event_unchanged, event_changed, event_returned],
    )

    created_titles = {e.title for e in result if isinstance(e, CreateCalendarEvent)}
    assert "Bibo: New Book" in created_titles
    assert "Bibo: Unchanged Book" not in created_titles
    assert len([e for e in result if isinstance(e, CreateCalendarEvent)]) == 1

    modified_ids = {e.event_id for e in result if isinstance(e, ModifyCalendarEvent)}
    assert "event-changed" in modified_ids
    assert "event-unchanged" not in modified_ids
    assert len([e for e in result if isinstance(e, ModifyCalendarEvent)]) == 1

    deleted_ids = {e.event_id for e in result if isinstance(e, DeleteCalendarEvent)}
    assert "event-returned" in deleted_ids
    assert "event-unchanged" not in deleted_ids
    assert len([e for e in result if isinstance(e, DeleteCalendarEvent)]) == 1
