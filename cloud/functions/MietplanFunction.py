from datetime import timedelta
import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.usecases import resolve_mietplan_service
from cloud.functions.infrastructure.telegram.models import (
    SendTelegramMessageEventGrid,
)
from cloud.functions.infrastructure.telegram.helper import (
    telegram_output_binding,
)
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.Mietplan,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@telegram_output_binding()
def check_mietplan(
    mytimer: TimerRequest,
    telegramOutput: Out[EventGridOutputEvent],
) -> None:
    try:
        logging.info("Checking for new mietplan files")
        service = resolve_mietplan_service()
        result = service.process_new_files(max_file_age=timedelta(days=1))

        if result.has_errors():
            error_message = f"Mietplan check failed:\n{result.errors_string}"
            logging.error(error_message)
            telegramOutput.set(
                SendTelegramMessageEventGrid(message=error_message).to_output()
            )
            return

        if not result.item:
            logging.info("No new mietplan files found")
            return

        message = _create_telegram_message(result.item)
        logging.info(f"Found {len(result.item)} new mietplan file(s)")
        telegramOutput.set(SendTelegramMessageEventGrid(message=message).to_output())

    except Exception as e:
        error_message = f"Mietplan function failed: {e}"
        logging.error(error_message, exc_info=True)
        telegramOutput.set(
            SendTelegramMessageEventGrid(message=error_message).to_output()
        )


def _create_telegram_message(uploaded_files: list[str]) -> str:
    message = "Found new mietplan files:\n" + "\n".join(
        [f"- {file}" for file in uploaded_files]
    )
    return message
