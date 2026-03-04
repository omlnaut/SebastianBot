import azure.functions as func

from cloud.dependencies import usecases
from cloud.functions.side_effects.shared import perform_usecase

from .models import CompleteTaskEventGrid
from function_app import app


@app.event_grid_trigger(arg_name="azeventgrid")  # type: ignore
def complete_task(
    azeventgrid: func.EventGridEvent,
):
    def create_request(event: CompleteTaskEventGrid) -> usecases.complete_task.Request:
        return usecases.complete_task.Request(
            tasklist=event.tasklist, task_id=event.task_id
        )

    perform_usecase(
        create_request,
        usecases.resolve_complete_task,
        azeventgrid,
    )
