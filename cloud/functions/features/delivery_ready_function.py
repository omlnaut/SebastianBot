import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_delivery_ready
from cloud.functions.side_effects.shared import (
    perform_usecase_from_request,
)
from function_app import app
from sebastian.usecases.features import delivery_ready

from ..TriggerTimes import TriggerTimes


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

    perform_usecase_from_request(
        delivery_ready.Request(hours_back=1), resolve_delivery_ready
    )
