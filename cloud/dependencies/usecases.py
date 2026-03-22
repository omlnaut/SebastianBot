from sebastian.protocols.gemini import IGeminiClient
from sebastian.protocols.google_drive import IGoogleDriveClient
from sebastian.protocols.manga_update import IMangaUpdateClient
from sebastian.protocols.mietplan import IMietplanClient
from sebastian.usecases.MangaUpdate.service import MangaUpdateService
from sebastian.usecases.mietplan.service import MietplanService
from sebastian.usecases.ReturnTracker.service import ReturnTrackerService
from sebastian.usecases.WinSim.service import WinSimService
from sebastian.usecases.side_effects import (
    complete_task,
    create_task,
    send_telegram_message,
    modify_mail_labels,
)
from sebastian.usecases.features import delivery_ready
from sebastian.usecases.features import bibo_lending_sync
import sebastian.usecases.WinSim as WinSim
import sebastian.usecases.ReturnTracker as ReturnTracker
from sebastian.usecases.usecase_handler import UseCaseHandler


from .clients import (
    resolve_bibo_client,
    resolve_gemini_client,
    resolve_gmail_client,
    resolve_google_drive_client,
    resolve_google_task_client,
    resolve_mangaupdate_client,
    resolve_mietplan_client,
    resolve_telegram_client,
)


def resolve_mietplan_service(
    mietplan_client: IMietplanClient | None = None,
    google_drive_client: IGoogleDriveClient | None = None,
    gdrive_folder_id: str = "19gdVV_DMtdQU0xi7TgfKJCRRc4c7m0fd",
) -> MietplanService:
    return MietplanService(
        mietplan_client=mietplan_client or resolve_mietplan_client(),
        google_drive_client=google_drive_client or resolve_google_drive_client(),
        gdrive_folder_id=gdrive_folder_id,
    )


def resolve_mangaupdate_service(
    mangaupdate_client: IMangaUpdateClient | None = None,
) -> MangaUpdateService:
    return MangaUpdateService(
        client=mangaupdate_client or resolve_mangaupdate_client(),
    )


def resolve_delivery_ready(
    gmail_client: delivery_ready.GmailClient | None = None,
) -> UseCaseHandler[delivery_ready.Request]:
    return delivery_ready.Handler(
        gmail_client=gmail_client or resolve_gmail_client(),
    )


def resolve_bibo_lending_sync(
    bibo_client: bibo_lending_sync.BiboClient | None = None,
    task_client: bibo_lending_sync.TaskClient | None = None,
) -> UseCaseHandler[bibo_lending_sync.Request]:
    return bibo_lending_sync.Handler(
        bibo_client=bibo_client or resolve_bibo_client(),
        task_client=task_client or resolve_google_task_client(),
    )


def resolve_winsim_service(
    gmail_client: WinSim.GmailClient | None = None,
    drive_client: IGoogleDriveClient | None = None,
) -> WinSimService:
    winsim_folder_id = "1VGX5Wt8D3huZm3vVemjI3C6zz6W38PJr"
    return WinSimService(
        gmail_client=gmail_client or resolve_gmail_client(),
        drive_client=drive_client or resolve_google_drive_client(),
        winsim_folder_id=winsim_folder_id,
    )


def resolve_return_tracker_service(
    gmail_client: ReturnTracker.GmailClient | None = None,
    gemini_client: IGeminiClient | None = None,
) -> ReturnTrackerService:
    return ReturnTrackerService(
        gmail_client=gmail_client or resolve_gmail_client(),
        gemini_client=gemini_client or resolve_gemini_client(),
    )


def resolve_modify_mail_label(
    gmail_client: modify_mail_labels.GmailClient | None = None,
) -> modify_mail_labels.Handler:
    return modify_mail_labels.Handler(
        gmail_client=gmail_client or resolve_gmail_client()
    )


def resolve_complete_task(
    task_client: complete_task.TaskClient | None = None,
) -> UseCaseHandler[complete_task.Request]:
    return complete_task.Handler(
        task_client=task_client or resolve_google_task_client(),
    )


def resolve_create_task(
    task_client: create_task.TaskClient | None = None,
) -> UseCaseHandler[create_task.Request]:
    return create_task.Handler(
        task_client=task_client or resolve_google_task_client(),
    )


def resolve_send_telegram_message(
    telegram_client: send_telegram_message.TelegramClient | None = None,
) -> UseCaseHandler[send_telegram_message.Request]:
    return send_telegram_message.Handler(
        telegram_client=telegram_client or resolve_telegram_client(),
    )
