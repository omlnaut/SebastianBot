from datetime import timedelta
import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_winsim
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import winsim

from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.WinSim,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_winsim_invoices(mytimer: TimerRequest) -> None:
    logging.info("WinSim timer function processed a request.")
    perform_usecase_from_request(
        winsim.Request(time_back=timedelta(hours=24)), resolve_winsim
    )
