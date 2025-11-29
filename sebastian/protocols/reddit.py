from typing import Protocol

from sebastian.clients.reddit.models import RedditPost


class RedditClientProtocol(Protocol):
    """Protocol for Reddit client operations."""

    def get_posts(self, subreddit: str) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        ...
