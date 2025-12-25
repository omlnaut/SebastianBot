from sebastian.protocols.reddit import IRedditClient, RedditComment
from sebastian.shared.dates import is_at_most_one_day_old

CHAPTER_BASE_URL = "demonicscans.org/title/Skeleton-Soldier"
SUBREDDIT_NAME = "SkeletonSoldier"


def _is_new_chapter_comment(comment: RedditComment) -> bool:
    return is_at_most_one_day_old(comment.created_at) and CHAPTER_BASE_URL in comment.text


class SkeletonSoldierService:
    def __init__(self, reddit_client: IRedditClient):
        self.reddit_client = reddit_client

    def get_new_chapter_comments(self) -> list[RedditComment]:
        new_comments = self.reddit_client.get_comments(SUBREDDIT_NAME, limit=100)
        return [comment for comment in new_comments if _is_new_chapter_comment(comment)]
