import logging

from azure.functions import TimerRequest

from function_app import app

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
    logging.info(
        "DeliveryReady legacy timer is disabled. Delivery mail processing now runs via central mail_check."
    )
