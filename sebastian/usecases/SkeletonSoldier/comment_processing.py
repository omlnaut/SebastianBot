from datetime import timedelta

from sebastian.protocols.reddit import RedditComment
from sebastian.shared.dates import is_at_most_one_day_old


def _extract_demonic_scans_link(comments: list[RedditComment]) -> str | None:
    """
    Extract link to demonic scans from comments posted in the last 24 hours.
    
    Args:
        comments: List of comments to search through
        
    Returns:
        URL to demonic scans if found, None otherwise
    """
    demonic_scans_domain = "demonicscans.org"
    
    for comment in comments:
        # Check if comment is at most 24 hours old
        if not is_at_most_one_day_old(comment.created_at_datetime):
            continue
        
        # Check if comment body contains link to demonic scans
        if demonic_scans_domain in comment.body.lower():
            # Extract URL from comment body
            words = comment.body.split()
            for word in words:
                if demonic_scans_domain in word.lower():
                    # Clean up the URL (remove trailing punctuation)
                    url = word.rstrip(".,;:!?)")
                    if url.startswith("http"):
                        return url
    
    return None
