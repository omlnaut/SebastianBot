from datetime import date

from cloud.dependencies.clients import resolve_calendar_event_client
from sebastian.domain.calendar import Calendars
from sebastian.domain.date_filter import DateFilter


def test_timerange():
    # Arrange
    client = resolve_calendar_event_client()

    # Act
    date_filter = DateFilter.from_dates(start=date(2026, 1, 1), end=date(2026, 1, 31))
    events = client.get_events(Calendars.Primary, date_filter=date_filter)

    # Assert
    assert len(events) == 5


def test_query():
    # Arrange
    client = resolve_calendar_event_client()

    # Act
    date_filter = DateFilter.from_dates(start=date(2026, 1, 1), end=date(2026, 1, 31))
    events = client.get_events(Calendars.Primary, q="1337", date_filter=date_filter)

    # Assert
    assert len(events) == 1
    event = events[0]
    assert event.description is not None
    assert "1337" in event.description
