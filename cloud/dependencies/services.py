from sebastian.clients.google.drive.client import GoogleDriveClient
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.google.task.client import GoogleTaskClient
from sebastian.clients.MangaUpdate.client import MangaUpdateClient
from sebastian.clients.mietplan.client.client import MietplanClient
from sebastian.clients.reddit.client import RedditClient
from sebastian.infrastructure.google.task.service import TaskService
from sebastian.usecases.DeliveryReady.service import DeliveryReadyService
from sebastian.usecases.MangaUpdate.service import MangaUpdateService
from sebastian.usecases.mietplan.service import MietplanService
from sebastian.usecases.OnePunchMan.service import OnePunchManService
from sebastian.usecases.SkeletonSoldier import SkeletonSoldierService
from sebastian.usecases.WinSim.service import WinSimService
from sebastian.usecases.ReturnTracker.service import ReturnTrackerService

from .clients import (
    resolve_gmail_client,
    resolve_google_drive_client,
    resolve_google_task_client,
    resolve_mangaupdate_client,
    resolve_mietplan_client,
    resolve_reddit_client,
)


def resolve_mietplan_service(
    mietplan_client: MietplanClient = resolve_mietplan_client(),
    google_drive_client: GoogleDriveClient = resolve_google_drive_client(),
    gdrive_folder_id: str = "19gdVV_DMtdQU0xi7TgfKJCRRc4c7m0fd",
) -> MietplanService:
    return MietplanService(
        mietplan_client=mietplan_client,
        google_drive_client=google_drive_client,
        gdrive_folder_id=gdrive_folder_id,
    )


def resolve_skeleton_soldier_service(
    reddit_client: RedditClient = resolve_reddit_client(),
) -> SkeletonSoldierService:
    return SkeletonSoldierService(
        reddit_client=reddit_client,
    )


def resolve_mangaupdate_service(
    mangaupdate_client: MangaUpdateClient = resolve_mangaupdate_client(),
) -> MangaUpdateService:
    return MangaUpdateService(
        client=mangaupdate_client,
    )


def resolve_one_punch_man_service(
    reddit_client: RedditClient = resolve_reddit_client(),
) -> OnePunchManService:
    return OnePunchManService(
        reddit_client=reddit_client,
    )


def resolve_delivery_ready_service(
    gmail_client: GmailClient = resolve_gmail_client(),
) -> DeliveryReadyService:
    return DeliveryReadyService(
        gmail_client=gmail_client,
    )


def resolve_google_task_service(
    task_client: GoogleTaskClient = resolve_google_task_client(),
) -> TaskService:
    return TaskService(
        client=task_client,
    )


def resolve_winsim_service(
    gmail_client: GmailClient = resolve_gmail_client(),
    drive_client: GoogleDriveClient = resolve_google_drive_client(),
) -> WinSimService:
    winsim_folder_id = "1VGX5Wt8D3huZm3vVemjI3C6zz6W38PJr"
    return WinSimService(
        gmail_client=gmail_client,
        drive_client=drive_client,
        winsim_folder_id=winsim_folder_id,
    )


def resolve_return_tracker_service(
    gmail_client: GmailClient = resolve_gmail_client(),
) -> ReturnTrackerService:
    return ReturnTrackerService(gmail_client=gmail_client)
