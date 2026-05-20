from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from sebastian.domain.task import TaskTags

_TRACKING_PREFIX = "Tracking:"
_PICKUP_LOCATION_PREFIX = "Abholort:"
_DUE_DATE_PREFIX = "Bis:"


class PickupDataLike(Protocol):
    item: str
    pickup_location: str
    due_date: date | None
    tracking_number: str | None


@dataclass(frozen=True)
class DeliveryReadyTaskNote:
    item: str | None
    pickup_location: str | None
    due_date: date | None
    tracking_number: str | None
    has_delivery_ready_tag: bool

    @classmethod
    def from_pickup_data(cls, pickup_data: PickupDataLike) -> "DeliveryReadyTaskNote":
        tracking_number = pickup_data.tracking_number
        return cls(
            item=pickup_data.item,
            pickup_location=pickup_data.pickup_location,
            due_date=pickup_data.due_date,
            tracking_number=tracking_number.upper() if tracking_number else None,
            has_delivery_ready_tag=True,
        )

    @classmethod
    def from_text(cls, text: str | None) -> "DeliveryReadyTaskNote":
        if text is None:
            return cls(
                item=None,
                pickup_location=None,
                due_date=None,
                tracking_number=None,
                has_delivery_ready_tag=False,
            )

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        item: str | None = None
        pickup_location: str | None = None
        due_date: date | None = None
        tracking_number: str | None = None

        for line in lines:
            if line.startswith(_PICKUP_LOCATION_PREFIX):
                pickup_location = line.removeprefix(_PICKUP_LOCATION_PREFIX).strip() or None
                continue

            if line.startswith(_DUE_DATE_PREFIX):
                raw_due_date = line.removeprefix(_DUE_DATE_PREFIX).strip()
                try:
                    due_date = date.fromisoformat("-".join(reversed(raw_due_date.split("."))))
                except ValueError:
                    due_date = None
                continue

            if line.startswith(_TRACKING_PREFIX):
                raw_tracking_number = line.removeprefix(_TRACKING_PREFIX).strip()
                tracking_number = raw_tracking_number.upper() if raw_tracking_number else None
                continue

            if line == TaskTags.DeliveryReady.value:
                continue

            if item is None:
                item = line

        return cls(
            item=item,
            pickup_location=pickup_location,
            due_date=due_date,
            tracking_number=tracking_number,
            has_delivery_ready_tag=TaskTags.DeliveryReady.value in lines,
        )

    def to_text(self) -> str:
        lines: list[str] = []
        if self.item:
            lines.append(self.item)
        if self.pickup_location:
            lines.append(f"{_PICKUP_LOCATION_PREFIX} {self.pickup_location}")
        if self.due_date:
            lines.append(f"{_DUE_DATE_PREFIX} {self.due_date.strftime('%d.%m.%Y')}")
        if self.tracking_number:
            lines.append(f"{_TRACKING_PREFIX} {self.tracking_number.upper()}")
        if self.has_delivery_ready_tag:
            lines.append(TaskTags.DeliveryReady.value)

        return "\n".join(lines)
