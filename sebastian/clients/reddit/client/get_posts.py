import requests

from sebastian.clients.reddit.models import RedditPost


def build_subreddit_url(subreddit: str) -> str:
    post_base_url = "https://oauth.reddit.com/r/{subreddit}/new.json?limit=100"
    url = post_base_url.format(subreddit=subreddit)
    return url


def get_raw_post_response(url: str, access_token: str, user_agent: str) -> dict:
    """Get raw post response from Reddit."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def parse_posts(subreddit: str, raw_posts: dict) -> list[RedditPost]:
    """Parse raw post data into RedditPost objects."""
    posts_data = raw_posts.get("data", {}).get("children", [])
    return [
        RedditPost(
            subreddit=subreddit,
            created_at_timestamp=post["data"]["created_utc"],
            title=post["data"]["title"],
            flair=post["data"].get("link_flair_text"),
            destination_url=post["data"].get("url", None),
        )
        for post in posts_data
    ]
