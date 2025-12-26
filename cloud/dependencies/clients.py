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
from sebastian.clients.reddit.client import RedditClient
from sebastian.clients.reddit.credentials import RedditCredentials
from sebastian.clients.telegram.client import TelegramClient
from sebastian.clients.telegram.config import TelegramConfig


def resolve_gmail_client() -> GmailClient:
    credentials = load_google_credentials()
    return GmailClient(credentials)


def resolve_reddit_client() -> RedditClient:
    credentials = get_secret(SecretKeys.RedditCredentials, RedditCredentials)
    return RedditClient(credentials)


def resolve_mangaupdate_client() -> MangaUpdateClient:
    credentials = get_secret(SecretKeys.MangaUpdateCredentials, MangaUpdateSecret)
    return MangaUpdateClient(credentials)


def resolve_telegram_client() -> TelegramClient:
    cloud_config = get_secret(SecretKeys.TelegramSebastianToken, CloudTelegramConfig)
    config = TelegramConfig(
        token=cloud_config.tokens[TelegramToken.Sebastian].token,
        chat_id=cloud_config.chats[TelegramChat.MainChat].id,
    )
    return TelegramClient(config)


def resolve_google_task_client() -> GoogleTaskClient:
    credentials = load_google_credentials()
    return GoogleTaskClient(credentials)


def resolve_google_drive_client() -> GoogleDriveClient:
    credentials = load_google_credentials()
    return GoogleDriveClient(credentials)


def resolve_mietplan_client() -> MietplanClient:
    credentials = get_secret(SecretKeys.MietplanCredentials, MietplanCredentials)
    return MietplanClient(credentials)


def resolve_gemini_client() -> GeminiClient:
    credentials = get_secret(SecretKeys.GeminiApiKey, GeminiApiKey)
    return GeminiClient(credentials)
