from function_app import app


def all_actor_output_binding(arg_name: str = "taskOutput"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="create_task",
        topic_endpoint_uri="ALLACTOR_EVENT_GRID_URI",
        topic_key_setting="ALLACTOR_EVENT_GRID_KEY",
    )
