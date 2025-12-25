from typing import Any, Iterator
from datetime import datetime, timezone

from praw.models.comment_forest import MoreComments
from praw.models.reddit.comment import Comment

from sebastian.protocols.reddit import RedditComment


def _parse_comment(comment: Comment | MoreComments) -> RedditComment | None:
    """Parse a Reddit comment into a RedditComment object."""
    match comment:
        case MoreComments():
            return None
        case Comment():
            return RedditComment(
                text=comment.body,
                created_at=datetime.fromtimestamp(comment.created_utc, timezone.utc),
            )


def _parse_comments(comments: Iterator[Any]) -> list[RedditComment]:
    """Parse Reddit comments into RedditComment objects."""
    return [
        parsed_comment
        for comment in comments
        if (parsed_comment := _parse_comment(comment)) is not None
    ]
