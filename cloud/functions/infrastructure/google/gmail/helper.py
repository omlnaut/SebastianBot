from function_app import app


def modify_mail_label_output_binding(arg_name: str = "modifyMailLabelOutput"):
    """Create an Event Grid output binding for modify mail label events.

    This helper configures an Azure Functions Event Grid output binding used to
    publish `modify_mail_label` events. The binding relies on the following
    environment variables to resolve the target Event Grid topic:

    - ``MODIFYMAILLABEL_EVENT_GRID_URI``: the Event Grid topic endpoint URI.
    - ``MODIFYMAILLABEL_EVENT_GRID_KEY``: the Event Grid topic access key.

    Args:
        arg_name: Name of the function argument that will use this output binding.

    Returns:
        The configured Event Grid output binding.
    """
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="modify_mail_label",
        topic_endpoint_uri="MODIFYMAILLABEL_EVENT_GRID_URI",
        topic_key_setting="MODIFYMAILLABEL_EVENT_GRID_KEY",
    )
