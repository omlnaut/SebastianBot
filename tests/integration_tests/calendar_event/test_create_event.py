from datetime import date

from cloud.dependencies.clients import resolve_calendar_event_client
from sebastian.domain.calendar import Calendars


def test_create_event_with_description():
    # Arrange
    client = resolve_calendar_event_client()
    test_title = "[CREATE TEST] integration test create_event with description"
    test_date = date(2026, 4, 15)
    test_description = "book_id: 123456789\ntitle: Some Book\nlocation: Shelf A"

    # Act
    client.create_event(
        Calendars.Primary, test_title, test_date, description=test_description
    )

    # Assert
    events = client.get_events(Calendars.Primary, q=test_title, time_min=test_date)
    assert len(events) == 1
    event = events[0]
    assert event.description is not None
    assert "book_id: 123456789" in event.description
    assert "title: Some Book" in event.description
    assert "location: Shelf A" in event.description

    # Cleanup
    client.delete_event(Calendars.Primary, event.id)
