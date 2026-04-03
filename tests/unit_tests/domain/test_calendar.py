import pytest
from pydantic import ValidationError

from sebastian.domain.calendar import Calendar


def test_calendar_creation_valid_data():
    # Arrange & Act
    calendar = Calendar(id="test@example.com", title="My Calendar")
    
    # Assert
    assert calendar.id == "test@example.com"
    assert calendar.title == "My Calendar"


def test_calendar_creation_invalid_email():
    # Arrange, Act & Assert
    with pytest.raises(ValidationError):
        Calendar(id="not-an-email", title="My Calendar")


def test_calendar_creation_empty_title():
    # Arrange, Act & Assert
    with pytest.raises(ValidationError):
        Calendar(id="test@example.com", title="")
