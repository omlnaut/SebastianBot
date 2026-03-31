import logging
from datetime import timedelta

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_return_tracker
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import return_tracker

from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.ReturnTracker,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_return_tracker(mytimer: TimerRequest) -> None:
    logging.info("ReturnTracker timer function processed a request.")
    perform_usecase_from_request(
        return_tracker.Request(time_back=timedelta(hours=1)),
        resolve_return_tracker,
    )
