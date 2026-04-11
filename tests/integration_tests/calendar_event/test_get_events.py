from datetime import date

from cloud.dependencies.clients import resolve_calendar_event_client
from sebastian.domain.calendar import Calendars


def test_timerange():
    # Arrange
    client = resolve_calendar_event_client()

    # Act
    events = client.get_events(
        Calendars.Primary, time_min=date(2026, 1, 1), time_max=date(2026, 1, 31)
    )

    # Assert
    assert len(events) == 3


def test_query():
    # Arrange
    client = resolve_calendar_event_client()

    # Act
    events = client.get_events(
        Calendars.Primary,
        q="1337",
        time_min=date(2026, 1, 1),
        time_max=date(2026, 1, 31),
    )

    # Assert
    assert len(events) == 1
    event = events[0]
    assert event.description is not None
    assert "1337" in event.description
