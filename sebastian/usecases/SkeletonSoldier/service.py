from sebastian.protocols.reddit import IRedditClient, RedditPost
from sebastian.shared.dates import is_at_most_one_day_old
from .comment_processing import _extract_demonic_scans_link


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
        posts = self.reddit_client.get_posts("SkeletonSoldier")
        new_chapter_posts = [post for post in posts if _is_new_chapter_post(post)]
        
        # Fetch comments for each new chapter post
        for post in new_chapter_posts:
            comments = self.reddit_client.get_post_comments(post.post_id, "SkeletonSoldier")
            post.comments = comments
            
            # Check if there's a demonic scans link in the comments
            demonic_scans_link = _extract_demonic_scans_link(comments)
            if demonic_scans_link:
                # Replace the destination URL with the demonic scans link
                post.destination_url = demonic_scans_link
        
        return new_chapter_posts
