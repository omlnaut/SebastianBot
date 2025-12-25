from sebastian.protocols.reddit.models import RedditPost


def has_flair(post: RedditPost, flair: str) -> bool:
    return post.flair is not None and post.flair.lower() == flair.lower()
