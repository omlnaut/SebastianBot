from cloud.functions.infrastructure.google.helper import load_google_credentials
from cloud.helper import SecretKeys, get_secret
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.MangaUpdate import MangaUpdateClient, MangaUpdateSecret
from sebastian.clients.reddit import RedditClient, RedditCredentials


def resolve_gmail_client() -> GmailClient:
    credentials = load_google_credentials()
    return GmailClient(credentials)


def resolve_reddit_client() -> RedditClient:
    credentials = get_secret(SecretKeys.RedditCredentials, RedditCredentials)
    return RedditClient(credentials)


def resolve_mangaupdate_client() -> MangaUpdateClient:
    credentials = get_secret(SecretKeys.MangaUpdateCredentials, MangaUpdateSecret)
    return MangaUpdateClient(credentials)
