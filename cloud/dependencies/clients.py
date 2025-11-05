from cloud.helper import SecretKeys, get_secret
from sebastian.clients.reddit import RedditClient, RedditCredentials


def resolve_reddit_client() -> RedditClient:
    credentials = get_secret(SecretKeys.RedditCredentials, RedditCredentials)
    return RedditClient(credentials)
