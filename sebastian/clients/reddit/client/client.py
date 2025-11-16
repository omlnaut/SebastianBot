import logging

from sebastian.clients.reddit.credentials import RedditCredentials
from sebastian.clients.reddit.models import RedditPost

from .auth import fetch_access_token
from .get_posts import build_subreddit_url, get_raw_post_response, parse_posts


class RedditClient:
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    POST_BASE_URL = "https://oauth.reddit.com/r/{subreddit}/new.json?limit=100"

    def __init__(self, credentials: RedditCredentials):
        self._credentials = credentials
        self._access_token: str | None = None

    def _get_token(self) -> str:
        if self._access_token is not None:
            return self._access_token
        self._access_token = fetch_access_token(self._credentials, self.TOKEN_URL)
        return self._access_token

    def get_posts(self, subreddit: str) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        logging.info(f"Fetching posts from subreddit: {subreddit}")
        url = build_subreddit_url(subreddit)
        raw_posts = get_raw_post_response(
            url, self._get_token(), self._credentials.user_agent
        )
        return parse_posts(subreddit, raw_posts)
