from sebastian.clients.reddit import RedditPost
from shared.dates import is_at_most_one_day_old


def is_new_chapter_post(post: RedditPost) -> bool:
    return (
        is_at_most_one_day_old(post.created_at_datetime)
        and post.flair is not None
        and post.flair.lower() == "new chapter"
    )
