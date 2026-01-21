from datetime import datetime
import json

import pytest
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
import azure.functions as func


@pytest.fixture
def test_start() -> datetime:
    """Fixture providing the test start time."""
    return datetime.now()


def _assert_base_fields(
    result: func.EventGridOutputEvent, test_start: datetime
) -> None:
    """Assert common fields for all EventGridOutputEvent results."""
    assert isinstance(result, func.EventGridOutputEvent)
    assert result.subject == "send_telegram_message"
    assert result.event_type == "send_telegram_message_event"
    assert result.event_time is not None
    assert result.event_time >= test_start
    assert result.data_version == "1.0"
    # ID should be a valid UUID
    assert len(result.id) == 36


def test_to_output_with_minimal_fields(test_start: datetime):
    """Test to_output with only required fields."""
    event = SendTelegramMessageEventGrid(message="Test message")
    result = event.to_output()

    _assert_base_fields(result, test_start)
    data = result.get_json()
    assert data["message"] == "Test message"


def test_to_output_with_long_message(test_start: datetime):
    """Test to_output with a long message."""
    long_message = "Test message " * 100
    event = SendTelegramMessageEventGrid(message=long_message)
    result = event.to_output()

    _assert_base_fields(result, test_start)
    data = result.get_json()
    assert data["message"] == long_message


def test_to_output_with_special_characters(test_start: datetime):
    """Test to_output with special characters in message."""
    special_message = "Test\nwith\ttabs\nand 👍 emojis"
    event = SendTelegramMessageEventGrid(message=special_message)
    result = event.to_output()

    _assert_base_fields(result, test_start)
    data = result.get_json()
    assert data["message"] == special_message


def test_to_output_data_is_model_dump(test_start: datetime):
    """Test that the data field correctly contains the model dump."""
    event = SendTelegramMessageEventGrid(message="Test message")
    result = event.to_output()
    expected_data = event.model_dump(mode="json")

    _assert_base_fields(result, test_start)
    assert result.get_json() == expected_data


def test_event_is_json_serializable(test_start: datetime):
    """Test that the event output can be serialized to JSON."""
    event = SendTelegramMessageEventGrid(
        message="Test message with special chars: \n\t👍"
    )
    result = event.to_output()

    # This will raise TypeError if any field is not JSON serializable
    json_string = json.dumps(result.get_json())
    assert json_string is not None

    # Verify we can deserialize it back
    parsed = json.loads(json_string)
    assert parsed["message"] == "Test message with special chars: \n\t👍"


def test_unique_event_ids():
    """Test that each to_output call generates a unique ID."""
    event = SendTelegramMessageEventGrid(message="Test message")
    result1 = event.to_output()
    result2 = event.to_output()

    assert result1.id != result2.id
