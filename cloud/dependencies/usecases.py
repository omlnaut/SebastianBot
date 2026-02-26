from sebastian.protocols.gemini import IGeminiClient
from sebastian.protocols.gmail import IGmailClient
from sebastian.protocols.google_drive import IGoogleDriveClient
from sebastian.protocols.manga_update import IMangaUpdateClient
from sebastian.protocols.mietplan import IMietplanClient
from sebastian.usecases.AddLabelToMail.handler import Handler as AddLabelToMail
from sebastian.usecases.AllHandler.MailToAllHandler.service import MailToAllHandler
from sebastian.usecases.AllHandler.service import AllHandlerService
from sebastian.usecases.DeliveryReady.service import DeliveryReadyService
from sebastian.usecases.MangaUpdate.service import MangaUpdateService
from sebastian.usecases.mietplan.service import MietplanService
from sebastian.usecases.ReturnTracker.service import ReturnTrackerService
from sebastian.usecases.WinSim.service import WinSimService
from sebastian.usecases.shared import UseCaseHandler
from sebastian.usecases.side_effects import complete_task, create_task


from .clients import (
    resolve_gemini_client,
    resolve_gmail_client,
    resolve_google_drive_client,
    resolve_google_task_client,
    resolve_mangaupdate_client,
    resolve_mietplan_client,
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


def resolve_delivery_ready_service(
    gmail_client: IGmailClient | None = None,
) -> DeliveryReadyService:
    return DeliveryReadyService(
        gmail_client=gmail_client or resolve_gmail_client(),
    )


def resolve_winsim_service(
    gmail_client: IGmailClient | None = None,
    drive_client: IGoogleDriveClient | None = None,
) -> WinSimService:
    winsim_folder_id = "1VGX5Wt8D3huZm3vVemjI3C6zz6W38PJr"
    return WinSimService(
        gmail_client=gmail_client or resolve_gmail_client(),
        drive_client=drive_client or resolve_google_drive_client(),
        winsim_folder_id=winsim_folder_id,
    )


def resolve_return_tracker_service(
    gmail_client: IGmailClient | None = None,
    gemini_client: IGeminiClient | None = None,
) -> ReturnTrackerService:
    return ReturnTrackerService(
        gmail_client=gmail_client or resolve_gmail_client(),
        gemini_client=gemini_client or resolve_gemini_client(),
    )


def resolve_allhandler_service(
    gmail_client: IGmailClient | None = None,
    gemini_client: IGeminiClient | None = None,
) -> AllHandlerService:
    return AllHandlerService(
        gmail=gmail_client or resolve_gmail_client(),
        gemini=gemini_client or resolve_gemini_client(),
    )


def resolve_allhandler_mail_service(
    gmail_client: IGmailClient | None = None,
    allhandler_service: AllHandlerService | None = None,
) -> "MailToAllHandler":
    return MailToAllHandler(
        mail_client=gmail_client or resolve_gmail_client(),
        all_handler_service=allhandler_service or resolve_allhandler_service(),
    )


def resolve_add_label_to_mail_service(
    gmail_client: IGmailClient | None = None,
) -> AddLabelToMail:
    return AddLabelToMail(gmail_client=gmail_client or resolve_gmail_client())


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
