from sebastian.usecases.SkeletonSoldier.service import _is_new_chapter_post
from sebastian.protocols.reddit.models import RedditPost
from datetime import datetime, timezone, timedelta
import pytest


@pytest.fixture
def today() -> int:
    return int((datetime.now(timezone.utc) - timedelta(hours=5)).timestamp())


@pytest.fixture
def in_past() -> int:
    return int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())


@pytest.fixture
def new_chapter_flair() -> str:
    return "New Chapter"


@pytest.fixture
def reddit_post(today: int, new_chapter_flair: str) -> RedditPost:
    return RedditPost(
        subreddit="SkeletonSoldier",
        created_at_timestamp=today,
        title="Test Post",
        flair=new_chapter_flair,
    )


def test_flair_is_none_returns_false(reddit_post: RedditPost):
    reddit_post.flair = None
    assert not _is_new_chapter_post(reddit_post)


def test_flair_is_not_new_chapter_returns_false(reddit_post: RedditPost):
    reddit_post.flair = "Some Other Flair"
    assert not _is_new_chapter_post(reddit_post)


def test_post_older_than_one_day_returns_false(reddit_post: RedditPost, in_past: int):
    reddit_post.created_at_timestamp = in_past
    assert not _is_new_chapter_post(reddit_post)


def test_flair_is_new_chapter_and_recent_returns_true(reddit_post: RedditPost):
    assert _is_new_chapter_post(reddit_post)


def test_flair_case_insensitivity(reddit_post: RedditPost):
    reddit_post.flair = "nEw ChApTeR"
    assert _is_new_chapter_post(reddit_post)
