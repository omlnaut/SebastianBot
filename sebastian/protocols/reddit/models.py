from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RedditComment:
    text: str
    created_at: datetime
    replies: list["RedditComment"]


@dataclass
class RedditPost:
    subreddit: str
    created_at: datetime
    title: str
    flair: str | None
    destination_url: str | None = None
    text: str | None = None
    comments: list[RedditComment] = field(default_factory=list)
