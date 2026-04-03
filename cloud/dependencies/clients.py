from functools import lru_cache

from google.oauth2.credentials import Credentials

from cloud.helper import SecretKeys, get_secret
from sebastian.clients.bibo.client import BiboClient
from sebastian.clients.google.calendar_event.client import CalendarEventClient
from sebastian.clients.google.drive.client import GoogleDriveClient
from sebastian.clients.google.gemini.client import GeminiClient
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.google.task.client import GoogleTaskClient
from sebastian.clients.MangaUpdate import MangaUpdateClient
from sebastian.clients.mietplan.client import MietplanClient
from sebastian.clients.telegram.client import TelegramClient


@lru_cache()
def load_google_credentials() -> Credentials:
    credentials_model = get_secret(SecretKeys.GoogleCredentials)
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
def resolve_google_task_client() -> GoogleTaskClient:
    credentials = load_google_credentials()
    return GoogleTaskClient(credentials)


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
def resolve_gemini_client() -> GeminiClient:
    credentials = get_secret(SecretKeys.GeminiApiKey)
    return GeminiClient(credentials)


@lru_cache()
def resolve_bibo_client() -> BiboClient:
    credentials = get_secret(SecretKeys.BiboCredentials)
    return BiboClient(credentials)
