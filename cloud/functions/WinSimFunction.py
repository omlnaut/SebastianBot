import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_winsim_service

from cloud.functions.side_effects.send_message.models import (
    SendTelegramMessageEventGrid,
)
from cloud.functions.side_effects.shared import send_eventgrid_events
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.WinSim,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_winsim_invoices(
    mytimer: TimerRequest,
) -> None:
    try:
        logging.info("WinSim timer function processed a request.")

        service = resolve_winsim_service()
        logging.info("Checking for recent WinSim invoices")
        uploads = service.process_recent_invoices(hours_back=24)

        logging.info(
            f"Successfully uploaded {len(uploads)} WinSim invoice(s) to Google Drive"
        )
        if (n_uploads := len(uploads)) > 0:
            success_msg = f"📄 WinSim: Uploaded {n_uploads} invoice(s) to Google Drive"
            send_eventgrid_events([SendTelegramMessageEventGrid(message=success_msg)])

    except Exception as e:
        error_msg = f"Error in check_winsim_invoices: {str(e)}"
        logging.error(error_msg)
        send_eventgrid_events([SendTelegramMessageEventGrid(message=error_msg)])
