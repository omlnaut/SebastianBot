from datetime import datetime, timedelta
import logging
from cloud.dependencies.services import resolve_allhandler_service
from cloud.functions.TriggerTimes import TriggerTimes
from cloud.functions.infrastructure.AllHandler.helper import allhandler_output_binding
from cloud.functions.infrastructure.AllHandler.models import AllHandlerEvent
from cloud.functions.infrastructure.telegram.helper import telegram_output_binding
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEvent
from function_app import app

from azure.functions import EventGridOutputEvent, Out, TimerRequest


@app.timer_trigger(
    schedule=TriggerTimes.MailCheck,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@telegram_output_binding()
@allhandler_output_binding()
def gmail_check_function(
    mytimer: TimerRequest,
    telegramOutput: Out[EventGridOutputEvent],
    allHandlerOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("GmailCheck timer function processed a request.")

        service = resolve_allhandler_service()
        logging.info("Checking for new emails")
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        results = service.process_all_emails(after=five_minutes_ago)

        errors = []
        success = []

        for result in results:
            if result.has_errors():
                error_msg = f"Error processing email: {result.errors_string}"
                logging.error(error_msg)
                errors.append(SendTelegramMessageEvent(message=error_msg))
            else:
                event = result.item
                assert event is not None
                if event.is_empty():
                    logging.info("No events to process in this email, skipping.")
                    continue
                api_event = AllHandlerEvent.from_application(event)
                success.append(api_event)

        telegramOutput.set([event.to_output() for event in errors])  # type: ignore
        allHandlerOutput.set([event.to_output() for event in success])  # type: ignore

    except Exception as e:
        error_msg = f"Error in gmail_check_function: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEvent(message=error_msg).to_output())
