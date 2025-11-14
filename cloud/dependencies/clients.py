from cloud.functions.infrastructure.google.helper import load_google_credentials
from cloud.functions.infrastructure.telegram.config import TelegramConfig
from cloud.helper import SecretKeys, get_secret
from sebastian.clients.google.drive.client import GoogleDriveClient
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.google.task.client import GoogleTaskClient
from sebastian.clients.MangaUpdate import MangaUpdateClient, MangaUpdateSecret
from sebastian.clients.reddit import RedditClient, RedditCredentials
from sebastian.clients.telegram.client import TelegramClient


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
    config = get_secret(SecretKeys.TelegramSebastianToken, TelegramConfig)
    return TelegramClient(config)


def resolve_google_task_client() -> GoogleTaskClient:
    credentials = load_google_credentials()
    return GoogleTaskClient(credentials)


def resolve_google_drive_client() -> GoogleDriveClient:
    credentials = load_google_credentials()
    return GoogleDriveClient(credentials)
