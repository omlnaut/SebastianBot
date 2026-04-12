import azure.functions as func

from cloud.dependencies import usecases
from cloud.functions.side_effects.shared import perform_usecase_from_eventgrid
from function_app import app

from .models import DeleteCalendarEventEventGrid


@app.event_grid_trigger(arg_name="azeventgrid")  # type: ignore
def delete_calendar_event(
    azeventgrid: func.EventGridEvent,
):
    def create_request(
        event: DeleteCalendarEventEventGrid,
    ) -> usecases.delete_calendar_event.Request:
        return usecases.delete_calendar_event.Request(
            calendar=event.calendar,
            event_id=event.event_id,
        )

    perform_usecase_from_eventgrid(
        create_request,
        usecases.resolve_delete_calendar_event,
        azeventgrid,
    )
