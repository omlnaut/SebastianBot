import logging

import azure.functions as func

from cloud.dependencies import usecases
from cloud.functions.side_effects.shared import (
    perform_usecase_from_eventgrid,
    send_eventgrid_events,
)
from sebastian.domain.task import TaskLists


from .models import CreateTaskEventGrid
from function_app import app


@app.route(route="test_create_task")
def test_create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP test - emit create task event")

    event_model = CreateTaskEventGrid(
        title="Sample Task", notes="Sample notes", tasklist=TaskLists.Mangas
    )
    send_eventgrid_events([event_model])
    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")  # type: ignore
def create_task(
    azeventgrid: func.EventGridEvent,
):
    def create_request(event: CreateTaskEventGrid) -> usecases.create_task.Request:
        return usecases.create_task.Request(
            tasklist=event.tasklist,
            title=event.title,
            notes=event.notes or "",
            due_date=event.due,
        )

    perform_usecase_from_eventgrid(
        create_request,
        usecases.resolve_create_task,
        azeventgrid,
    )
