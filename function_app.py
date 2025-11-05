import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

from cloud.functions import check_skeleton_soldier_updates
from infrastructure.google.task.TaskFunction import create_task, test_create_task
from infrastructure.telegram.TelegramFunction import (
    send_telegram_message,
    test_send_telegram_message,
)
from usecases.manga.manga_update.MangaUpdateFunction import check_manga_update
