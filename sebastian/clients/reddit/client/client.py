import logging
from typing import Callable

import praw

from .get_posts import _parse_posts
from .get_comments import _parse_comments
from sebastian.clients.reddit.credentials import RedditCredentials
from sebastian.protocols.reddit import RedditPost, RedditComment


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
    ) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        logging.info(f"Fetching posts from subreddit: {subreddit}")
        subreddit_obj = self._reddit.subreddit(subreddit)
        posts = subreddit_obj.new(limit=limit)
        return _parse_posts(posts)

    def get_comments(self, subreddit: str, limit: int) -> list[RedditComment]:
        """Fetch most recent comments from a subreddit."""
        logging.info(f"Fetching comments from subreddit: {subreddit}")
        subreddit_obj = self._reddit.subreddit(subreddit)
        comments = subreddit_obj.comments(limit=limit)
        return _parse_comments(comments)
