from dataclasses import dataclass
from datetime import datetime


@dataclass
class RedditComment:
    text: str
    created_at: datetime


@dataclass
class RedditPost:
    subreddit: str
    created_at: datetime
    title: str
    flair: str | None
    destination_url: str | None = None
    text: str | None = None

    def has_flair(self, flair: str) -> bool:
        return self.flair is not None and self.flair.lower() == flair.lower()
