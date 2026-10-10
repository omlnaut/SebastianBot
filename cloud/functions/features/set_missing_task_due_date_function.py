import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_set_missing_task_due_date
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import (
    set_missing_task_due_date as set_missing_task_due_date_usecase,
)

from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.SetMissingTaskDueDate,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def set_missing_task_due_date(mytimer: TimerRequest) -> None:
    logging.info("set_missing_task_due_date timer function processed a request.")

    perform_usecase_from_request(
        set_missing_task_due_date_usecase.Request(),
        resolve_set_missing_task_due_date,
    )
