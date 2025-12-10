import logging

import praw  # type: ignore

from .get_posts import _parse_posts
from sebastian.clients.reddit.credentials import RedditCredentials
from sebastian.clients.reddit.models import RedditPost


class RedditClient:
    def __init__(self, credentials: RedditCredentials):
        self._credentials = credentials
        self._reddit = praw.Reddit(
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            username=credentials.username,
            password=credentials.password,
            user_agent=credentials.user_agent,
        )

    def get_posts(self, subreddit: str) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        logging.info(f"Fetching posts from subreddit: {subreddit}")
        subreddit_obj = self._reddit.subreddit(subreddit)
        return _parse_posts(subreddit, subreddit_obj.new(limit=100))
