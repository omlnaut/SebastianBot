import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_check_parcel_received
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import (
    check_parcel_received as check_parcel_received_usecase,
)

from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.CheckParcelReceived,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_parcel_received(mytimer: TimerRequest) -> None:
    logging.info("check_parcel_received timer function processed a request.")

    perform_usecase_from_request(
        check_parcel_received_usecase.Request(),
        resolve_check_parcel_received,
    )
