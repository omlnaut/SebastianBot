from typing import Protocol

from sebastian.protocols.reddit.models import RedditPost


class IRedditClient(Protocol):
    """Protocol for Reddit client operations."""

    def get_posts(self, subreddit: str) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        ...
