from datetime import timedelta
import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.usecases import resolve_mietplan_service
from cloud.functions.infrastructure.AllActor.helper import all_actor_output_binding
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.Mietplan,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@all_actor_output_binding()
def check_mietplan(
    mytimer: TimerRequest,
    allActorOutput: Out[EventGridOutputEvent],
) -> None:
    logging.info("Checking for new mietplan files")

    service = resolve_mietplan_service()
    actor_result = service.process_new_files(max_file_age=timedelta(days=1))

    allActorOutput.set(AllActorEventGrid.from_application(actor_result).to_output())
