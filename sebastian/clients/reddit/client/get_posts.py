from typing import Any, Iterator

from sebastian.protocols.reddit.models import RedditPost


def _parse_posts(submissions: Iterator[Any]) -> list[RedditPost]:
    """Parse Reddit submissions into RedditPost objects."""
    return [
        RedditPost(
            subreddit=getattr(submission, "subreddit", "error fetching subreddit"),
            created_at_timestamp=int(submission.created_utc),
            title=submission.title,
            flair=getattr(submission, "link_flair_text", None),
            destination_url=getattr(submission, "url", None),
        )
        for submission in submissions
    ]
