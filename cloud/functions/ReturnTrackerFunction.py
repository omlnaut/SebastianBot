import logging
from datetime import timedelta

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_return_tracker_service
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from cloud.functions.side_effects.shared import send_eventgrid_events
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.ReturnTracker,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_return_tracker(
    mytimer: TimerRequest,
) -> None:
    logging.info("ReturnTracker timer function processed a request.")

    service = resolve_return_tracker_service()

    logging.info("Checking for recent Amazon return emails")
    actor_result = service.get_recent_returns(time_back=timedelta(hours=1))

    send_eventgrid_events([AllActorEventGrid.from_application(actor_result)])
