# pyright: standard
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

from cloud.functions.features.delivery_ready_function import check_delivery_ready
from cloud.functions.side_effects.complete_task.function import complete_task
from cloud.functions.side_effects.create_task.function import (
    create_task,
    test_create_task,
)
from cloud.functions.side_effects.send_message.function import (
    send_telegram_message,
    test_send_telegram_message,
)

from cloud.functions.side_effects.modify_mail_label.function import (
    modify_mail_label,
    test_modify_mail_label,
)
from cloud.functions.features.bibo_lending_sync_function import check_bibo_lending_sync
from cloud.functions.features.MangaUpdateFunction import check_manga_update
from cloud.functions.features.mietplan_function import check_mietplan
from cloud.functions.features.winsim_function import check_winsim_invoices
from cloud.functions.features.return_tracker_function import check_return_tracker
