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
