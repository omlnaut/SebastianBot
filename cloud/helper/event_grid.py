import uuid
from abc import ABC
from datetime import datetime

import azure.functions as func
from azure.eventgrid import EventGridEvent
from pydantic import BaseModel


class EventGridMixin:
    """Mixin that provides auto-generated to_output() method for EventGrid models.

    Automatically derives event subject and type from class name:
    - Removes "EventGrid" suffix if present
    - Converts CamelCase to snake_case
    - Example: ModifyMailLabelEventGrid -> subject: "modify_mail_label", event_type: "modify_mail_label_event"
    """

    @property
    def base_name(self):
        return self.__class__.__name__.replace("EventGrid", "")

    @classmethod
    def uri_env_name(cls) -> str:
        return f"{cls.__name__.replace('EventGrid', '').upper()}_EVENT_GRID_URI"

    @classmethod
    def key_env_name(cls) -> str:
        return f"{cls.__name__.replace('EventGrid', '').upper()}_EVENT_GRID_KEY"

    def to_output(self) -> func.EventGridOutputEvent:
        """Generate EventGridOutputEvent with auto-derived configuration."""
        # Derive base name from class name (remove EventGrid suffix)
        base_name = self.base_name

        return func.EventGridOutputEvent(
            id=str(uuid.uuid4()),
            data=self.model_dump(mode="json"),  # type: ignore
            subject=base_name,
            event_type=f"{base_name}_event",
            event_time=datetime.now(),
            data_version="1.0",
        )

    def to_direct_output(self) -> EventGridEvent:
        """Generate EventGridEvent for SDK with auto-derived configuration."""
        # Derive base name from class name (remove EventGrid suffix)
        base_name = self.base_name

        return EventGridEvent(
            subject=base_name,
            event_type=f"{base_name}_event",
            data=self.model_dump(mode="json"),  # type: ignore
            data_version="1.0",
        )


class EventGridModel(BaseModel, EventGridMixin, ABC):
    pass
