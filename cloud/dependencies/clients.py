from functools import lru_cache

from google.oauth2.credentials import Credentials
from cloud.helper import SecretKeys, get_secret
from sebastian.clients.bibo.client import BiboClient
from sebastian.clients.deepseek.client import DeepSeekClient
from sebastian.clients.dhl.client import DhlClient
from sebastian.domain.bibo import BiboAccounts
from sebastian.domain.task import GoogleTaskAccount
from sebastian.clients.google.calendar_event.client import CalendarEventClient
from sebastian.clients.google.drive.client import GoogleDriveClient
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.google.task.client import GoogleTaskClient
from sebastian.clients.MangaUpdate import MangaUpdateClient
from sebastian.clients.mietplan.client import MietplanClient
from sebastian.clients.telegram.client import TelegramClient


@lru_cache()
def load_google_credentials(
    account: GoogleTaskAccount = GoogleTaskAccount.Original,
) -> Credentials:
    match account:
        case GoogleTaskAccount.Original:
            key = SecretKeys.GoogleCredentials
        case GoogleTaskAccount.Second:
            key = SecretKeys.GoogleCredentialsSecond
        case _:
            raise ValueError(f"Unknown Google task account: {account}")
    credentials_model = get_secret(key)
    creds = Credentials.from_authorized_user_info(credentials_model.credentials.model_dump())  # type: ignore
    return creds


@lru_cache()
def resolve_gmail_client() -> GmailClient:
    credentials = load_google_credentials()
    return GmailClient(credentials)


@lru_cache()
def resolve_mangaupdate_client() -> MangaUpdateClient:
    credentials = get_secret(SecretKeys.MangaUpdateCredentials)
    return MangaUpdateClient(credentials)


@lru_cache()
def resolve_telegram_client() -> TelegramClient:
    config = get_secret(SecretKeys.TelegramSebastianToken)
    return TelegramClient(config)


@lru_cache()
def resolve_google_task_client(
    account: GoogleTaskAccount = GoogleTaskAccount.Original,
) -> GoogleTaskClient:
    credentials = (
        load_google_credentials()
        if account == GoogleTaskAccount.Original
        else load_google_credentials(account)
    )
    return GoogleTaskClient(
        credentials, use_account_default=account == GoogleTaskAccount.Second
    )


@lru_cache()
def resolve_calendar_event_client() -> CalendarEventClient:
    credentials = load_google_credentials()
    return CalendarEventClient(credentials)


@lru_cache()
def resolve_google_drive_client() -> GoogleDriveClient:
    credentials = load_google_credentials()
    return GoogleDriveClient(credentials)


@lru_cache()
def resolve_mietplan_client() -> MietplanClient:
    credentials = get_secret(SecretKeys.MietplanCredentials)
    return MietplanClient(credentials)


@lru_cache()
def resolve_deepseek_client() -> DeepSeekClient:
    credentials = get_secret(SecretKeys.DeepSeekCredentials)
    return DeepSeekClient(credentials)


@lru_cache()
def resolve_bibo_client(bibo_account: BiboAccounts) -> BiboClient:
    credentials = get_secret(SecretKeys.BiboCredentials)
    account_credentials = credentials.accounts[bibo_account.value]
    return BiboClient(account_credentials)


@lru_cache()
def resolve_dhl_client() -> DhlClient:
    return DhlClient()
