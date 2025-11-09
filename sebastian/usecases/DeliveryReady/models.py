from dataclasses import dataclass


@dataclass
class PickupData:
    tracking_number: str | None
    pickup_location: str
    due_date: str | None
    preview: str | None
