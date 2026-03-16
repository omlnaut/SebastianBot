import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_delivery_ready
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from cloud.functions.side_effects.shared import send_eventgrid_events
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.DeliveryReady,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_delivery_ready(
    mytimer: TimerRequest,
) -> None:
    logging.info("DeliveryReady timer function processed a request.")

    service = resolve_delivery_ready()

    logging.info("Checking for recent DHL pickups")
    actor_result = service.get_recent_dhl_pickups(hours_back=1)

    send_eventgrid_events([AllActorEventGrid.from_application(actor_result)])
