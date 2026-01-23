import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.usecases import resolve_winsim_service
from cloud.functions.infrastructure.telegram.models import (
    SendTelegramMessageEventGrid,
)
from cloud.functions.infrastructure.telegram.helper import (
    telegram_output_binding,
)
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.WinSim,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@telegram_output_binding()
def check_winsim_invoices(
    mytimer: TimerRequest,
    telegramOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("WinSim timer function processed a request.")

        service = resolve_winsim_service()
        logging.info("Checking for recent WinSim invoices")
        result = service.process_recent_invoices(hours_back=24)

        if result.item:
            logging.info(
                f"Successfully uploaded {len(result.item)} WinSim invoice(s) to Google Drive"
            )
            success_msg = (
                f"📄 WinSim: Uploaded {len(result.item)} invoice(s) to Google Drive"
            )
            telegramOutput.set(
                SendTelegramMessageEventGrid(message=success_msg).to_output()
            )

        if result.errors:
            logging.error(f"Errors occurred: {result.errors_string}")
            telegramOutput.set(
                SendTelegramMessageEventGrid(message=result.errors_string).to_output()
            )

    except Exception as e:
        error_msg = f"Error in check_winsim_invoices: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEventGrid(message=error_msg).to_output())
