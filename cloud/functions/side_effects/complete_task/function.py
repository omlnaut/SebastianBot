import azure.functions as func

from azure.functions import EventGridOutputEvent, Out

from cloud.dependencies import usecases
from cloud.functions.infrastructure.AllActor.helper import all_actor_output_binding
from cloud.functions.side_effects.shared import perform_usecase

from .models import CompleteTaskEventGrid
from function_app import app

# todo: sort imports


@app.event_grid_trigger(arg_name="azeventgrid")
@all_actor_output_binding()
def complete_task(
    azeventgrid: func.EventGridEvent,
    allActorOutput: Out[EventGridOutputEvent],
):
    def create_request(event: CompleteTaskEventGrid) -> usecases.complete_task.Request:
        return usecases.complete_task.Request(
            tasklist_id=event.tasklist_id, task_id=event.task_id
        )

    actor_result = perform_usecase(
        CompleteTaskEventGrid,
        create_request,
        usecases.resolve_complete_task,
        azeventgrid,
        allActorOutput,
    )
