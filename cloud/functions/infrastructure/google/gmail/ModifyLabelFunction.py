import logging

import azure.functions as func

from cloud.dependencies.usecases import resolve_add_label_to_mail_service
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
from cloud.functions.side_effects.shared import send_eventgrid_events
from cloud.helper import parse_payload
from function_app import app
from sebastian.protocols.gmail import GmailLabel

from .models import ModifyMailLabelEventGrid


@app.route(route="test_modify_mail_label")
def test_modify_mail_label(
    req: func.HttpRequest,
) -> func.HttpResponse:
    logging.info("HTTP test - emit modify mail label event")

    event_model = ModifyMailLabelEventGrid(
        email_id="19bec88a8ef4ddd4",  # taken from test_labels.py
        add_labels=[GmailLabel.ToRead],
    )
    send_eventgrid_events([event_model])

    return func.HttpResponse("emitted")


@app.event_grid_trigger(arg_name="azeventgrid")
def modify_mail_label(
    azeventgrid: func.EventGridEvent,
):
    try:
        logging.info("EventGrid modify_mail_label triggered")
        event = parse_payload(azeventgrid, ModifyMailLabelEventGrid)

        logging.info(
            f"Modifying labels for email: {event.email_id}. Adding: {event.add_labels}, Removing: {event.remove_labels}"
        )

        service = resolve_add_label_to_mail_service()
        result = service.modify_labels(
            email_id=event.email_id,
            add_labels=event.add_labels,
            remove_labels=event.remove_labels,
        )

        if result.has_errors():
            error_msg = f"Error modifying labels: {result.errors_string}"
            logging.error(error_msg)
            send_eventgrid_events([SendTelegramMessageEventGrid(message=error_msg)])
        else:
            logging.info(
                f"Successfully modified labels for email: {event.email_id}. Added: {event.add_labels}, Removed: {event.remove_labels}"
            )

    except Exception as e:
        error_msg = f"Error in modify_mail_label: {str(e)}"
        logging.error(error_msg)
        send_eventgrid_events([SendTelegramMessageEventGrid(message=error_msg)])
