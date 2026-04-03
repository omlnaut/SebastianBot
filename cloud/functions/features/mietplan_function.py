import logging
from datetime import timedelta

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_mietplan
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import mietplan

from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.Mietplan,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_mietplan(
    mytimer: TimerRequest,
) -> None:
    logging.info("Checking for new mietplan files")

    perform_usecase_from_request(
        mietplan.Request(max_file_age=timedelta(days=1)), resolve_mietplan
    )
