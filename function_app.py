import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

from cloud.functions.DeliveryReadyFunction import check_delivery_ready
from cloud.functions.infrastructure.google.task import create_task, test_create_task
from cloud.functions.infrastructure.telegram.function import (
    send_telegram_message,
    test_send_telegram_message,
)
from cloud.functions.MangaUpdateFunction import check_manga_update
from cloud.functions.MietplanFunction import check_mietplan
from cloud.functions.OnePunchManFunction import check_one_punch_man_updates
from cloud.functions.SkeletonSoldierFunction import check_skeleton_soldier_updates
from cloud.functions.WinSimFunction import check_winsim_invoices
from cloud.functions.ReturnTrackerFunction import check_return_tracker
