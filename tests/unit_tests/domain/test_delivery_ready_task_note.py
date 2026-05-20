from datetime import date

from sebastian.domain.delivery_ready_task_note import DeliveryReadyTaskNote
from sebastian.usecases.features.delivery_ready.parsing import PickupData


def test_delivery_ready_task_note_round_trip_encode_decode():
    pickup = PickupData(
        tracking_number="ab12cd34",
        pickup_location="Packstation 123",
        due_date=date(2026, 5, 20),
        item="Book",
    )

    note = DeliveryReadyTaskNote.from_pickup_data(pickup).to_text()
    parsed = DeliveryReadyTaskNote.from_text(note)

    assert parsed.item == "Book"
    assert parsed.pickup_location == "Packstation 123"
    assert parsed.due_date == date(2026, 5, 20)
    assert parsed.tracking_number == "AB12CD34"
    assert parsed.has_delivery_ready_tag is True


def test_delivery_ready_task_note_missing_tracking_number():
    text = """Book
Abholort: Packstation 123
Bis: 20.05.2026
DELIVERY_READY"""

    parsed = DeliveryReadyTaskNote.from_text(text)

    assert parsed.tracking_number is None
    assert parsed.has_delivery_ready_tag is True


def test_delivery_ready_task_note_tag_detection():
    with_tag = DeliveryReadyTaskNote.from_text("Book\nDELIVERY_READY")
    without_tag = DeliveryReadyTaskNote.from_text("Book")

    assert with_tag.has_delivery_ready_tag is True
    assert without_tag.has_delivery_ready_tag is False


def test_delivery_ready_task_note_normalizes_tracking_number_to_uppercase():
    parsed = DeliveryReadyTaskNote.from_text("Tracking: ab12cd34\nDELIVERY_READY")

    assert parsed.tracking_number == "AB12CD34"
