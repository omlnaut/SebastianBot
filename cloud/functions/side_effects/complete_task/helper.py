from function_app import app


def complete_task_output_binding(arg_name: str = "completeTaskOutput"):
    # todo: create env vars
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="complete_task",
        topic_endpoint_uri="COMPLETETASK_EVENT_GRID_URI",
        topic_key_setting="COMPLETETASK_EVENT_GRID_KEY",
    )
