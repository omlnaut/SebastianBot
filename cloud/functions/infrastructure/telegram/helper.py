from function_app import app


def telegram_output_binding(arg_name="telegramOutput"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="send_telegram_message",
        topic_endpoint_uri="SENDTELEGRAMMESSAGE_EVENT_GRID_URI",
        topic_key_setting="SENDTELEGRAMMESSAGE_EVENT_GRID_KEY",
    )
