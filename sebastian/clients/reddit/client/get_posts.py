from typing import Any, Callable, Iterator
from datetime import datetime, timezone
from praw.models.comment_forest import MoreComments
from praw.models.reddit.comment import Comment

from sebastian.protocols.reddit import RedditPost, RedditComment


def _parse_posts(
    submissions: Iterator[Any], post_filter: Callable[[RedditPost], bool] | None = None
) -> list[RedditPost]:
    """Parse Reddit submissions into RedditPost objects."""
    return [
        post
        for submission in submissions
        if _is_valid_post(post := _parse_post_from_submission(submission), post_filter)
    ]


def _is_valid_post(
    post: RedditPost, post_filter: Callable[[RedditPost], bool] | None
) -> bool:
    if post_filter is None:
        return True
    return post_filter(post)


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
