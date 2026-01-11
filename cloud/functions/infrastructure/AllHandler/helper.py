from function_app import app


def allhandler_output_binding(arg_name="allHandlerOutput"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="trigger_all_handler",
        topic_endpoint_uri="TRIGGER_ALL_HANDLER_EVENT_GRID_URI",
        topic_key_setting="TRIGGER_ALL_HANDLER_EVENT_GRID_KEY",
    )
