import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

from cloud.functions.infrastructure.google.task import create_task, test_create_task
from cloud.functions.infrastructure.telegram import (
    send_telegram_message,
    test_send_telegram_message,
)
from cloud.functions.MangaUpdateFunction import check_manga_update
from cloud.functions.OnePunchManFunction import check_one_punch_man_updates
from cloud.functions.SkeletonSoldierFunction import check_skeleton_soldier_updates
