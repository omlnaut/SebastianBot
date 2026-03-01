from datetime import datetime, timedelta
import logging

import azure.functions as func

from cloud.dependencies.usecases import (
    resolve_add_label_to_mail_service,
    resolve_allhandler_mail_service,
)
from cloud.functions.TriggerTimes import TriggerTimes
from cloud.functions.infrastructure.AllHandler.models import AllHandlerEventGrid
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.functions.side_effects.shared import send_eventgrid_events
from cloud.helper import parse_payload
from function_app import app

from azure.functions import TimerRequest


@app.timer_trigger(
    schedule=TriggerTimes.MailCheck,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def gmail_check_function(
    mytimer: TimerRequest,
) -> None:
    try:
        logging.info("GmailCheck timer function processed a request.")

        service = resolve_allhandler_mail_service()
        logging.info("Checking for new emails")
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        results = service.process_recent_emails(after=five_minutes_ago)

        errors = []
        success = []

        for result in results:
            if result.has_errors():
                error_msg = f"Error processing email: {result.errors_string}"
                logging.error(error_msg)
                errors.append(SendTelegramMessageEventGrid(message=error_msg))
            else:
                event = result.item
                assert event is not None
                if event.is_empty():
                    logging.info("No events to process in this email, skipping.")
                    continue
                api_event = AllHandlerEventGrid.from_application(event)
                success.append(api_event)

        send_eventgrid_events(errors)
        send_eventgrid_events(success)

    except Exception as e:
        error_msg = f"Error in gmail_check_function: {str(e)}"
        logging.error(error_msg)
        send_eventgrid_events([SendTelegramMessageEventGrid(message=error_msg)])
