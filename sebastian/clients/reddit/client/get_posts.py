from typing import Any, Callable, Iterator
from datetime import datetime, timezone
from praw.models.comment_forest import MoreComments
from praw.models.reddit.comment import Comment

from sebastian.protocols.reddit import RedditPost, RedditComment


def _parse_posts(submissions: Iterator[Any]) -> list[RedditPost]:
    """Parse Reddit submissions into RedditPost objects."""
    return [_parse_post_from_submission(submission) for submission in submissions]


def _parse_post_from_submission(submission: Any) -> RedditPost:
    post = RedditPost(
        subreddit=getattr(submission, "subreddit", "error fetching subreddit"),
        created_at=datetime.fromtimestamp(submission.created_utc, timezone.utc),
        title=submission.title,
        flair=getattr(submission, "link_flair_text", None),
        destination_url=getattr(submission, "url", None),
        text=getattr(submission, "selftext", None),
    )

    return post
