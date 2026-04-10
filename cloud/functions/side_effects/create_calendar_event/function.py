import logging
from datetime import date

import azure.functions as func

from cloud.dependencies import usecases
from cloud.functions.side_effects.shared import (
    perform_usecase_from_eventgrid,
    send_eventgrid_events,
)
from function_app import app
from sebastian.domain.calendar import Calendars

from .models import CreateCalendarEventEventGrid


@app.route(route="test_create_calendar_event")
def test_create_calendar_event(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP test - emit create calendar event")

    event_model = CreateCalendarEventEventGrid(
        calendar=Calendars.Primary, title="Test Event", date=date.today()
    )
    send_eventgrid_events([event_model])
    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")  # type: ignore
def create_calendar_event(
    azeventgrid: func.EventGridEvent,
):
    def create_request(
        event: CreateCalendarEventEventGrid,
    ) -> usecases.create_calendar_event.Request:
        return usecases.create_calendar_event.Request(
            calendar=event.calendar,
            title=event.title,
            date=event.date,
        )

    perform_usecase_from_eventgrid(
        create_request,
        usecases.resolve_create_calendar_event,
        azeventgrid,
    )
