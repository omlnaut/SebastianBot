from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RedditComment:
    body: str
    created_at_timestamp: int

    @property
    def created_at_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.created_at_timestamp, timezone.utc)


@dataclass
class RedditPost:
    subreddit: str
    created_at_timestamp: int
    title: str
    flair: str | None
    post_id: str
    destination_url: str | None = None
    comments: list[RedditComment] = field(default_factory=list)

    @property
    def created_at_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.created_at_timestamp, timezone.utc)

    @property
    def created_at(self) -> str:
        return self.created_at_datetime.strftime("%Y-%m-%d")
