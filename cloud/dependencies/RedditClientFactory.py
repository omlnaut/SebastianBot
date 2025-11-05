from sebastian.clients.reddit import RedditClient, RedditCredentials
from shared.secrets import SecretKeys, get_secret


def RedditClientFromSecret() -> RedditClient:
    credentials = get_secret(SecretKeys.RedditCredentials, RedditCredentials)
    return RedditClient(credentials)
