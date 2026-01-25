from function_app import app


def modify_mail_label_output_binding(arg_name: str = "modifyMailLabelOutput"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="modify_mail_label",
        topic_endpoint_uri="MODIFYMAILLABEL_EVENT_GRID_URI",
        topic_key_setting="MODIFYMAILLABEL_EVENT_GRID_KEY",
    )
