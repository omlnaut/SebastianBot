import logging
from datetime import timedelta

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.usecases import resolve_return_tracker_service
from cloud.functions.infrastructure.AllActor.helper import all_actor_output_binding
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.ReturnTracker,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@all_actor_output_binding()
def check_return_tracker(
    mytimer: TimerRequest,
    allActorOutput: Out[EventGridOutputEvent],
) -> None:
    logging.info("ReturnTracker timer function processed a request.")

    service = resolve_return_tracker_service()

    logging.info("Checking for recent Amazon return emails")
    actor_result = service.get_recent_returns(time_back=timedelta(hours=1))

    allActorOutput.set(AllActorEventGrid.from_application(actor_result).to_output())
