from typing import Any, Callable, Iterator
from datetime import datetime, timezone
from praw.models.comment_forest import MoreComments
from praw.models.reddit.comment import Comment

from sebastian.protocols.reddit import RedditPost, RedditComment


def _parse_comment(comment: Comment | MoreComments) -> RedditComment | None:
    """Parse a Reddit comment into a RedditComment object recursively."""
    # Parse replies recursively
    match comment:
        case MoreComments():
            return None
        case Comment():
            return RedditComment(
                text=comment.body,
                created_at=datetime.fromtimestamp(comment.created_utc, timezone.utc),
            )


def _parse_posts(
    submissions: Iterator[Any], post_filter: Callable[[RedditPost], bool] | None = None
) -> list[RedditPost]:
    """Parse Reddit submissions into RedditPost objects."""
    posts = []
    for submission in submissions:
        post = _parse_post_from_submission(submission)

        if not _is_valid_post(post, post_filter):
            continue

        post.comments = _parse_comments_from_submission(submission)
        posts.append(post)

    return posts


def _parse_comments_from_submission(submission: Any) -> list[RedditComment]:
    submission.comments.replace_more(limit=0)
    comments = [
        parsed_comment
        for comment in submission.comments.list()
        if (parsed_comment := _parse_comment(comment)) is not None
    ]

    return comments


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
