import azure.functions as func

from cloud.dependencies import usecases
from cloud.functions.side_effects.shared import perform_usecase_from_eventgrid
from function_app import app

from .models import ModifyCalendarEventEventGrid


@app.event_grid_trigger(arg_name="azeventgrid")  # type: ignore
def modify_calendar_event(
    azeventgrid: func.EventGridEvent,
):
    def create_request(
        event: ModifyCalendarEventEventGrid,
    ) -> usecases.modify_calendar_event.Request:
        return usecases.modify_calendar_event.Request(
            calendar=event.calendar,
            event_id=event.event_id,
            date=event.date,
        )

    perform_usecase_from_eventgrid(
        create_request,
        usecases.resolve_modify_calendar_event,
        azeventgrid,
    )
