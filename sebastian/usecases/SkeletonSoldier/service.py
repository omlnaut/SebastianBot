from sebastian.protocols.reddit import IRedditClient, RedditPost
from sebastian.shared.dates import is_at_most_one_day_old


def _is_new_chapter_post(post: RedditPost) -> bool:
    return (
        is_at_most_one_day_old(post.created_at_datetime)
        and post.flair is not None
        and post.flair.lower() == "new chapter"
    )


class SkeletonSoldierService:
    def __init__(self, reddit_client: IRedditClient):
        self.reddit_client = reddit_client

    def get_new_chapter_posts(self) -> list[RedditPost]:
        posts = self.reddit_client.get_posts(
            "SkeletonSoldier", limit=100, post_filter=_is_new_chapter_post
        )
        return posts
