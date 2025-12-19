import logging
from typing import Any

from sebastian.protocols.reddit import RedditComment


def _parse_comments(submission: Any) -> list[RedditComment]:
    """Parse Reddit comments into RedditComment objects."""
    comments = []
    
    # Flatten comment tree to get all comments
    submission.comments.replace_more(limit=0)  # Remove "load more comments" objects
    
    for comment in submission.comments.list():
        try:
            comments.append(
                RedditComment(
                    body=comment.body,
                    created_at_timestamp=int(comment.created_utc),
                )
            )
        except AttributeError as e:
            # Skip comments that don't have required attributes
            logging.warning(f"Skipping comment due to missing attributes: {e}")
            continue
    
    return comments
