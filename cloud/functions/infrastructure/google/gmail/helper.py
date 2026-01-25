from function_app import app


def modify_mail_label_output_binding(arg_name: str = "modifyMailLabelOutput"):
    # TODO: Set up environment variables:
    # - MODIFY_MAIL_LABEL_EVENT_GRID_URI
    # - MODIFY_MAIL_LABEL_EVENT_GRID_KEY
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="modify_mail_label",
        topic_endpoint_uri="MODIFY_MAIL_LABEL_EVENT_GRID_URI",
        topic_key_setting="MODIFY_MAIL_LABEL_EVENT_GRID_KEY",
    )
