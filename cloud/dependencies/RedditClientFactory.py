from cloud.helper import SecretKeys, get_secret
from sebastian.clients.reddit import RedditClient, RedditCredentials


def RedditClientFromSecret() -> RedditClient:
    credentials = get_secret(SecretKeys.RedditCredentials, RedditCredentials)
    return RedditClient(credentials)
