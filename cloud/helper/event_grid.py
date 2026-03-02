import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Self, TypeVar

import azure.functions as func
from azure.eventgrid import EventGridEvent
from pydantic import BaseModel, Field, field_validator


class EventGridInfo(BaseModel):
    uri: str = Field(..., min_length=1)
    key: str = Field(..., min_length=1)

    @field_validator("uri")
    @classmethod
    def validate_uri_https(cls, v: str) -> str:
        https_prefix = "https://"
        if not v.startswith(https_prefix):
            raise ValueError(f"uri must start with '{https_prefix}'")

        event_grid_part = ".eventgrid.azure.net"
        if event_grid_part not in v:
            raise ValueError(f"uri must contain '{event_grid_part}'")
        return v


TRequest = TypeVar("TRequest", bound=BaseModel)


class EventGridMixin[TRequest](ABC):
    """Mixin that provides auto-generated to_output() method for EventGrid models.

    Automatically derives event subject and type from class name:
    - Removes "EventGrid" suffix if present
    - Converts CamelCase to snake_case
    - Example: ModifyMailLabelEventGrid -> subject: "modify_mail_label", event_type: "modify_mail_label_event"
    """

    @classmethod
    @abstractmethod
    def from_application(cls, app_event: TRequest) -> Self:
        """Create EventGrid model from application-layer model.

        Each subclass must implement this class method to convert from
        application-layer types (e.g., SendMessage, CreateTask) to EventGrid models.

        Returns:
            An instance of the concrete EventGrid model class.
        """
        ...

    @property
    def base_name(self):
        return self.__class__.__name__.replace("EventGrid", "")

    @classmethod
    def uri_env_name(cls) -> str:
        return f"{cls.__name__.replace('EventGrid', '').upper()}_EVENT_GRID_URI"

    @classmethod
    def key_env_name(cls) -> str:
        return f"{cls.__name__.replace('EventGrid', '').upper()}_EVENT_GRID_KEY"

    @classmethod
    def env_name(cls) -> str:
        return f"{cls.__name__}"

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


class EventGridModel[TRequest](BaseModel, EventGridMixin[TRequest], ABC):
    pass
