import logging
from datetime import timedelta

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.services import resolve_return_tracker_service
from cloud.functions.infrastructure.google.task import (
    task_output_binding,
)
from cloud.functions.infrastructure.google.task.CreateTaskEvent import CreateTaskEvent
from cloud.functions.infrastructure.telegram.helper import (
    SendTelegramMessageEvent,
    telegram_output_binding,
)
from function_app import app
from sebastian.protocols.google_task import TaskListIds
from sebastian.usecases.ReturnTracker.models import ReturnData

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.ReturnTracker,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@task_output_binding()
@telegram_output_binding()
def check_return_tracker(
    mytimer: TimerRequest,
    taskOutput: Out[EventGridOutputEvent],
    telegramOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("ReturnTracker timer function processed a request.")

        service = resolve_return_tracker_service()
        logging.info("Checking for recent Amazon return emails")
        result = service.get_recent_returns(time_back=timedelta(hours=1))

        logging.info(
            f"Found {len(result.item) if result.item else 0} recent Amazon returns"
        )

        if result.item:
            tasks = [_map_to_task_event(r).to_output() for r in result.item]
            taskOutput.set(tasks)  # type: ignore
            logging.info(f"Created {len(tasks)} task(s) for returns")

        if result.errors:
            logging.error(f"Errors occurred: {result.errors_string}")
            telegramOutput.set(
                SendTelegramMessageEvent(message=result.errors_string).to_output()
            )

    except Exception as e:
        error_msg = f"Error in return_tracker: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())


def _map_to_task_event(return_data: ReturnData) -> CreateTaskEvent:
    title = "Retoure"
    notes = (
        f"{return_data.item_title}\n"
        f"Abholort: {return_data.pickup_location}\n"
        f"Retoure bis: {return_data.return_date}\n"
        f"Order: {return_data.order_number}"
    )
    return CreateTaskEvent(title=title, notes=notes, task_list_id=TaskListIds.Default)
