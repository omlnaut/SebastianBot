from sebastian.usecases.SkeletonSoldier.service import _is_new_chapter_comment
from sebastian.protocols.reddit.models import RedditComment
from datetime import datetime, timezone, timedelta
import pytest


@pytest.fixture
def today() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=5)


@pytest.fixture
def in_past() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=2)


@pytest.fixture
def chapter_url() -> str:
    return "demonicscans.org/title/Skeleton-Soldier"


@pytest.fixture
def reddit_comment(today: datetime, chapter_url: str) -> RedditComment:
    return RedditComment(
        text=f"New chapter is out! Check it here: {chapter_url}/chapter-123",
        created_at=today,
    )


def test_comment_without_chapter_url_returns_false(reddit_comment: RedditComment):
    reddit_comment.text = "Just a regular comment without the chapter link"
    assert not _is_new_chapter_comment(reddit_comment)


def test_comment_with_different_url_returns_false(reddit_comment: RedditComment):
    reddit_comment.text = "Check out this chapter at someothersite.com/skeleton-soldier"
    assert not _is_new_chapter_comment(reddit_comment)


def test_comment_older_than_one_day_returns_false(
    reddit_comment: RedditComment, in_past: datetime
):
    reddit_comment.created_at = in_past
    assert not _is_new_chapter_comment(reddit_comment)


def test_comment_with_chapter_url_and_recent_returns_true(
    reddit_comment: RedditComment,
):
    assert _is_new_chapter_comment(reddit_comment)


def test_chapter_url_can_appear_anywhere_in_text(
    reddit_comment: RedditComment, chapter_url: str
):
    reddit_comment.text = f"Hey everyone! {chapter_url}/ch-456 just dropped!"
    assert _is_new_chapter_comment(reddit_comment)
