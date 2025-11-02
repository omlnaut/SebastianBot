import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

from infrastructure.telegram.TelegramFunction import (
    send_telegram_message,
    test_send_telegram_message,
)
from infrastructure.google.task.TaskFunction import (
    create_task,
    test_create_task,
)
