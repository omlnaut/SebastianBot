import logging
from datetime import timedelta

import azure.functions as func
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
    _run_check_mietplan()


@app.route(route="check_mietplan")
def check_mietplan_http(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger: check_mietplan")
    _run_check_mietplan()
    return func.HttpResponse("check_mietplan executed", status_code=200)


def _run_check_mietplan() -> None:
    logging.info("Checking for new mietplan files")

    perform_usecase_from_request(
        mietplan.Request(max_file_age=timedelta(days=1)), resolve_mietplan
    )
