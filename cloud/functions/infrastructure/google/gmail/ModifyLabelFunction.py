import logging

import azure.functions as func

from cloud.dependencies.usecases import resolve_add_label_to_mail_service
from cloud.functions.infrastructure.telegram.helper import telegram_output_binding
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.helper import parse_payload
from function_app import app

from .models import ModifyMailLabelEventGrid


@app.event_grid_trigger(arg_name="azeventgrid")
@telegram_output_binding()
def modify_mail_label(
    azeventgrid: func.EventGridEvent,
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    try:
        logging.info("EventGrid modify_mail_label triggered")
        event = parse_payload(azeventgrid, ModifyMailLabelEventGrid)

        logging.info(f"Modifying labels for email: {event.email_id}")

        service = resolve_add_label_to_mail_service()
        result = service.modify_labels(
            email_id=event.email_id,
            add_labels=event.add_labels,
            remove_labels=event.remove_labels,
        )

        if result.has_errors():
            error_msg = f"Error modifying labels: {result.errors_string}"
            logging.error(error_msg)
            telegramOutput.set(
                SendTelegramMessageEventGrid(message=error_msg).to_output()
            )
        else:
            logging.info(f"Successfully modified labels for email: {event.email_id}")

    except Exception as e:
        error_msg = f"Error in modify_mail_label: {str(e)}"
        logging.error(error_msg)
        telegramOutput.set(SendTelegramMessageEventGrid(message=error_msg).to_output())
