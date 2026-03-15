import logging

import azure.functions as func

from cloud.dependencies.usecases import resolve_modify_mail_label
from cloud.functions.side_effects.shared import perform_usecase, send_eventgrid_events
from function_app import app
from sebastian.domain.gmail import GmailLabel
from sebastian.usecases.side_effects import modify_mail_labels

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


@app.event_grid_trigger(arg_name="azeventgrid")  # type: ignore
def modify_mail_label(
    azeventgrid: func.EventGridEvent,
):
    def _create_request(event: ModifyMailLabelEventGrid) -> modify_mail_labels.Request:
        return modify_mail_labels.Request(
            email_id=event.email_id,
            add_labels=event.add_labels,
            remove_labels=event.remove_labels,
        )

    perform_usecase(_create_request, resolve_modify_mail_label, azeventgrid)
