import logging
from typing import Callable

import praw

from .get_posts import _parse_posts
from sebastian.clients.reddit.credentials import RedditCredentials
from sebastian.protocols.reddit import RedditPost


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

    def get_posts(
        self,
        subreddit: str,
        limit: int,
        post_filter: Callable[[RedditPost], bool] | None = None,
    ) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        logging.info(f"Fetching posts from subreddit: {subreddit}")
        subreddit_obj = self._reddit.subreddit(subreddit)
        posts = subreddit_obj.new(limit=limit)
        return _parse_posts(posts, post_filter=post_filter)
