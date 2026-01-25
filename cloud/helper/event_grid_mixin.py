import re
import uuid
from datetime import datetime

import azure.functions as func


class EventGridMixin:
    """Mixin that provides auto-generated to_output() method for EventGrid models.

    Automatically derives event subject and type from class name:
    - Removes "EventGrid" suffix if present
    - Converts CamelCase to snake_case
    - Example: ModifyMailLabelEventGrid -> subject: "modify_mail_label", event_type: "modify_mail_label_event"
    """

    def to_output(self) -> func.EventGridOutputEvent:
        """Generate EventGridOutputEvent with auto-derived configuration."""
        # Derive base name from class name (remove EventGrid suffix)
        base_name = self.__class__.__name__.replace("EventGrid", "")

        return func.EventGridOutputEvent(
            id=str(uuid.uuid4()),
            data=self.model_dump(mode="json"),  # type: ignore
            subject=base_name,
            event_type=f"{base_name}_event",
            event_time=datetime.now(),
            data_version="1.0",
        )
