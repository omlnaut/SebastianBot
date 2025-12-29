import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.services import resolve_delivery_ready_service
from cloud.functions.infrastructure.google.task import (
    task_output_binding,
)
from cloud.functions.infrastructure.google.task.models import CreateTaskEvent
from cloud.functions.infrastructure.telegram.SendTelegramMessageEvent import (
    SendTelegramMessageEvent,
)
from cloud.functions.infrastructure.telegram.helper import (
    telegram_output_binding,
)
from function_app import app
from sebastian.protocols.google_task import TaskListIds
from sebastian.usecases.DeliveryReady.models import PickupData

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.DeliveryReady,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@task_output_binding()
@telegram_output_binding()
def check_delivery_ready(
    mytimer: TimerRequest,
    taskOutput: Out[EventGridOutputEvent],
    telegramOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("DeliveryReady timer function processed a request.")

        service = resolve_delivery_ready_service()
        logging.info("Checking for recent DHL pickups")
        result = service.get_recent_dhl_pickups(hours_back=1)

        logging.info(
            f"Found {len(result.item) if result.item else 0} recent DHL pickups"
        )

        if result.item:
            tasks = [_map_to_task_event(pickup).to_output() for pickup in result.item]
            taskOutput.set(tasks)  # type: ignore
            logging.info(f"Created {len(tasks)} task(s) for DHL pickups")

        if result.errors:
            logging.error(f"Errors occurred: {result.errors_string}")
            telegramOutput.set(
                SendTelegramMessageEvent(message=result.errors_string).to_output()
            )

    except Exception as e:
        error_msg = f"Error in delivery_ready: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())


def _map_to_task_event(pickup: PickupData) -> CreateTaskEvent:
    title = f"Paket abholen: {pickup.preview}"

    notes = ""
    if pickup.preview:
        notes += f"{pickup.preview}"
    notes += f"\nAbholort: {pickup.pickup_location}"
    if pickup.due_date:
        notes += f"\nBis: {pickup.due_date}"
    if pickup.tracking_number:
        notes += f"\nTracking: {pickup.tracking_number}"

    return CreateTaskEvent(title=title, notes=notes, task_list_id=TaskListIds.Default)
