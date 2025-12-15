from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class RedditPost:
    subreddit: str
    created_at_timestamp: int
    title: str
    flair: str | None
    destination_url: str | None = None

    @property
    def created_at_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.created_at_timestamp, timezone.utc)

    @property
    def created_at(self) -> str:
        return self.created_at_datetime.strftime("%Y-%m-%d")
