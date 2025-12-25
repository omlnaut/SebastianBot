from sebastian.protocols.reddit import IRedditClient, RedditPost
from sebastian.shared.dates import is_at_most_one_day_old

NEW_CHAPTER_FLAIR = "murata chapter"
SUBREDDIT_NAME = "OnePunchMan"


def _is_new_chapter_post(post: RedditPost) -> bool:
    return is_at_most_one_day_old(post.created_at) and post.has_flair(NEW_CHAPTER_FLAIR)


class OnePunchManService:
    def __init__(self, reddit_client: IRedditClient):
        self.reddit_client = reddit_client

    def get_new_chapter_posts(self) -> list[RedditPost]:
        new_posts = self.reddit_client.get_posts(SUBREDDIT_NAME, limit=100)
        return [post for post in new_posts if _is_new_chapter_post(post)]
