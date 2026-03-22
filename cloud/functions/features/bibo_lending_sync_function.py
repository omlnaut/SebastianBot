import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_bibo_lending_sync
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import bibo_lending_sync

from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.BiboLendingSync,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_bibo_lending_sync(mytimer: TimerRequest) -> None:
    logging.info("BiboLendingSync timer function processed a request.")

    perform_usecase_from_request(bibo_lending_sync.Request(), resolve_bibo_lending_sync)
