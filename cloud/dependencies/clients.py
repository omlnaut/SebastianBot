from functools import lru_cache

from cloud.functions.infrastructure.google.helper import load_google_credentials
from cloud.functions.infrastructure.telegram.config import (
    TelegramChat,
    TelegramConfig as CloudTelegramConfig,
    TelegramToken,
)
from cloud.helper import SecretKeys, get_secret
from sebastian.clients.google.drive.client import GoogleDriveClient
from sebastian.clients.google.gemini.client import GeminiClient
from sebastian.clients.google.gemini.credentials import GeminiApiKey
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.google.task.client import GoogleTaskClient
from sebastian.clients.MangaUpdate import MangaUpdateClient, MangaUpdateSecret
from sebastian.clients.mietplan.client import MietplanClient
from sebastian.clients.mietplan.credentials import MietplanCredentials
from sebastian.clients.telegram.client import TelegramClient
from sebastian.clients.telegram.config import TelegramConfig
from sebastian.protocols.gemini.IClient import IGeminiClient
from sebastian.protocols.gmail.IClient import IGmailClient
from sebastian.protocols.google_drive.IClient import IGoogleDriveClient
from sebastian.protocols.google_task.IClient import IGoogleTaskClient
from sebastian.protocols.manga_update.IClient import IMangaUpdateClient
from sebastian.protocols.mietplan.IClient import IMietplanClient
from sebastian.protocols.telegram.IClient import ITelegramClient


@lru_cache()
def resolve_gmail_client() -> IGmailClient:
    credentials = load_google_credentials()
    return GmailClient(credentials)


@lru_cache()
def resolve_mangaupdate_client() -> IMangaUpdateClient:
    credentials = get_secret(SecretKeys.MangaUpdateCredentials, MangaUpdateSecret)
    return MangaUpdateClient(credentials)


@lru_cache()
def resolve_telegram_client() -> ITelegramClient:
    cloud_config = get_secret(SecretKeys.TelegramSebastianToken, CloudTelegramConfig)
    config = TelegramConfig(
        token=cloud_config.tokens[TelegramToken.Sebastian].token,
        chat_id=cloud_config.chats[TelegramChat.MainChat].id,
    )
    return TelegramClient(config)


@lru_cache()
def resolve_google_task_client() -> IGoogleTaskClient:
    credentials = load_google_credentials()
    return GoogleTaskClient(credentials)


@lru_cache()
def resolve_google_drive_client() -> IGoogleDriveClient:
    credentials = load_google_credentials()
    return GoogleDriveClient(credentials)


@lru_cache()
def resolve_mietplan_client() -> IMietplanClient:
    credentials = get_secret(SecretKeys.MietplanCredentials, MietplanCredentials)
    return MietplanClient(credentials)


@lru_cache()
def resolve_gemini_client() -> IGeminiClient:
    credentials = get_secret(SecretKeys.GeminiApiKey, GeminiApiKey)
    return GeminiClient(credentials)
