from typing import get_type_hints

from cloud.functions.side_effects.shared import EVENT_MAP
from cloud.helper.event_grid import EventGridModel
from sebastian.protocols.models import BaseActorEvent


def test_all_base_actor_events_in_event_map():
    """Verify that every domain event subclassing BaseActorEvent is registered in the EVENT_MAP."""
    missing_events = [
        subclass
        for subclass in BaseActorEvent.__subclasses__()
        if subclass not in EVENT_MAP
    ]

    assert not missing_events, f"Missing events in EVENT_MAP: {missing_events}"


def test_event_map_values_match_generic_types():
    """Verify that the EventGridModel values in EVENT_MAP properly derive from EventGridModel[Key].

    Since extraction of the exact generic template argument type dynamically off `Pydantic` `BaseModel`
    is incredibly unstable natively, we resolve it predictably by cross-referencing against
    the `app_event` argument typed in the `.from_application()` abstract implementation.
    """
    for app_event_cls, event_grid_cls in EVENT_MAP.items():
        assert issubclass(
            event_grid_cls, EventGridModel
        ), f"{event_grid_cls} is not an EventGridModel"

        hints = get_type_hints(event_grid_cls.from_application)
        assert (
            "app_event" in hints
        ), f"{event_grid_cls}.from_application must have an 'app_event' parameter"

        implemented_type = hints["app_event"]
        assert implemented_type is app_event_cls, (
            f"Type mismatch in EVENT_MAP! Key is {app_event_cls.__name__}, "
            f"but value {event_grid_cls.__name__} implements .from_application() with {implemented_type.__name__}"
        )
