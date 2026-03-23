from cloud.dependencies.clients import resolve_calendar_event_client


def test_get_calendars_returns_at_least_one():
    # Arrange
    client = resolve_calendar_event_client()
    
    # Act
    calendars = client.get_calendars()
    
    # Assert
    assert len(calendars) >= 1
