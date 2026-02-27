import logging

import azure.functions as func

from cloud.dependencies import usecases
from cloud.functions.side_effects.shared import perform_usecase


from .models import CreateTaskEventGrid
from function_app import app
from sebastian.protocols.google_task import TaskListIds

from .helper import task_output_binding


@app.route(route="test_create_task")
@task_output_binding()
def test_create_task(
    req: func.HttpRequest, taskOutput: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("HTTP test - emit create task event")

    event_model = CreateTaskEventGrid(
        title="Sample Task", notes="Sample notes", task_list_id=TaskListIds.Mangas
    )
    taskOutput.set(event_model.to_output())

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
def create_task(
    azeventgrid: func.EventGridEvent,
):
    def create_request(event: CreateTaskEventGrid) -> usecases.create_task.Request:
        return usecases.create_task.Request(
            tasklist_id=event.task_list_id,
            title=event.title,
            notes=event.notes or "",
            due_date=event.due,
        )

    perform_usecase(
        create_request,
        usecases.resolve_create_task,
        azeventgrid,
    )
