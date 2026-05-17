from datetime import date

from cloud.dependencies.clients import resolve_calendar_event_client
from sebastian.domain.calendar import Calendars
from sebastian.domain.task import DateFilter


def test_modify_calendar_event():
    # Arrange
    client = resolve_calendar_event_client()
    test_title = "[MODIFY TEST] integration test modify_calendar_event"
    original_date = date(2026, 4, 20)
    new_date = date(2026, 4, 22)

    client.create_event(Calendars.Primary, test_title, original_date)
    date_filter_original = DateFilter.from_dates(start=original_date)
    events = client.get_events(
        Calendars.Primary, q=test_title, date_filter=date_filter_original
    )
    assert len(events) == 1
    event_id = events[0].id

    # Act
    client.modify_calendar_event(Calendars.Primary, event_id, new_date)

    # Assert
    date_filter_new = DateFilter.from_dates(start=new_date)
    events_after = client.get_events(
        Calendars.Primary, q=test_title, date_filter=date_filter_new
    )
    assert len(events_after) == 1
    assert events_after[0].start is not None
    assert events_after[0].start.date() == new_date

    # Cleanup
    client.delete_event(Calendars.Primary, event_id)
