import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_set_missing_task_due_date
from cloud.functions.side_effects.shared import SIDE_EFFECT_MAP, send_eventgrid_events
from cloud.functions.side_effects.send_message.models import SendTelegramMessageEventGrid
from function_app import app
from sebastian.domain.task import GoogleTaskAccount
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

    errors: list[SendTelegramMessageEventGrid] = []
    for account in GoogleTaskAccount:
        try:
            handler = resolve_set_missing_task_due_date(account=account)
            effects = handler.handle(
                set_missing_task_due_date_usecase.Request(account=account)
            )
            events = [
                SIDE_EFFECT_MAP[type(effect)].from_application(effect)
                for effect in effects
            ]
            if events:
                send_eventgrid_events(events)
        except Exception as error:
            message = (
                f"Error setting missing task due dates (account {account.value}): "
                f"{type(error).__name__}"
            )
            logging.error(message)
            errors.append(SendTelegramMessageEventGrid(message=message))
    if errors:
        send_eventgrid_events(errors)
