from typing import Callable, Protocol

from .models import RedditPost, RedditComment


class IRedditClient(Protocol):
    """Protocol for Reddit client operations."""

    def get_posts(
        self,
        subreddit: str,
        limit: int,
        post_filter: Callable[[RedditPost], bool] | None = None,
    ) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        ...

    def get_comments(self, subreddit: str, limit: int) -> list[RedditComment]:
        """Fetch most recent comments from a subreddit."""
        ...
