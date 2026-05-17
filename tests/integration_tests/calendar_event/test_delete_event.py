from datetime import date

from cloud.dependencies.clients import resolve_calendar_event_client
from sebastian.domain.calendar import Calendars
from sebastian.domain.task import DateFilter


def test_delete_event():
    # Arrange
    client = resolve_calendar_event_client()
    test_title = "[DELETE TEST] integration test delete_event"
    test_date = date(2026, 4, 15)
    client.create_event(Calendars.Primary, test_title, test_date)

    date_filter = DateFilter.from_dates(start=test_date)
    events = client.get_events(Calendars.Primary, q=test_title, date_filter=date_filter)
    assert len(events) == 1
    event_id = events[0].id

    # Act
    client.delete_event(Calendars.Primary, event_id)

    # Assert
    events_after = client.get_events(
        Calendars.Primary, q=test_title, date_filter=date_filter
    )
    assert len(events_after) == 0
