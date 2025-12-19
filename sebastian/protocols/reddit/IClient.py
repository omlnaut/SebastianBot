from typing import Protocol

from .models import RedditComment, RedditPost


class IRedditClient(Protocol):
    """Protocol for Reddit client operations."""

    def get_posts(self, subreddit: str) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        ...

    def get_post_comments(self, post_id: str, subreddit: str) -> list[RedditComment]:
        """Fetch comments for a specific post."""
        ...
