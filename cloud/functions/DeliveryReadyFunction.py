import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.usecases import resolve_delivery_ready_service
from cloud.functions.infrastructure.AllActor.helper import all_actor_output_binding
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.DeliveryReady,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@all_actor_output_binding()
def check_delivery_ready(
    mytimer: TimerRequest,
    allActorOutput: Out[EventGridOutputEvent],
) -> None:
    logging.info("DeliveryReady timer function processed a request.")

    service = resolve_delivery_ready_service()

    logging.info("Checking for recent DHL pickups")
    actor_result = service.get_recent_dhl_pickups(hours_back=1)

    allActorOutput.set(AllActorEventGrid.from_application(actor_result).to_output())
