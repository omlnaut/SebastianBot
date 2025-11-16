from sebastian.clients.reddit.client import RedditClient
from sebastian.clients.reddit.models import RedditPost
from sebastian.shared.dates import is_at_most_one_day_old


def _is_new_chapter_post(post: RedditPost) -> bool:
    return (
        is_at_most_one_day_old(post.created_at_datetime)
        and post.flair is not None
        and post.flair.lower() == "new chapter"
    )


class SkeletonSoldierService:
    def __init__(self, reddit_client: RedditClient):
        self.reddit_client = reddit_client

    def get_new_chapter_posts(self) -> list[RedditPost]:
        posts = self.reddit_client.get_posts("SkeletonSoldier")
        return [post for post in posts if _is_new_chapter_post(post)]
