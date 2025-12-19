from datetime import datetime, timedelta, timezone

from sebastian.protocols.reddit import RedditComment
from sebastian.usecases.SkeletonSoldier.comment_processing import (
    _extract_demonic_scans_link,
)


def test_extract_demonic_scans_link_with_valid_link():
    # Arrange
    now = datetime.now(timezone.utc)
    comments = [
        RedditComment(
            body="Check out the chapter here: https://demonicscans.org/chapter/123",
            created_at_timestamp=int(now.timestamp()),
        )
    ]

    # Act
    result = _extract_demonic_scans_link(comments)

    # Assert
    assert result == "https://demonicscans.org/chapter/123"


def test_extract_demonic_scans_link_with_trailing_punctuation():
    # Arrange
    now = datetime.now(timezone.utc)
    comments = [
        RedditComment(
            body="Here's the link: https://demonicscans.org/chapter/456.",
            created_at_timestamp=int(now.timestamp()),
        )
    ]

    # Act
    result = _extract_demonic_scans_link(comments)

    # Assert
    assert result == "https://demonicscans.org/chapter/456"


def test_extract_demonic_scans_link_with_old_comment():
    # Arrange
    two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
    comments = [
        RedditComment(
            body="Check out the chapter here: https://demonicscans.org/chapter/789",
            created_at_timestamp=int(two_days_ago.timestamp()),
        )
    ]

    # Act
    result = _extract_demonic_scans_link(comments)

    # Assert
    assert result is None


def test_extract_demonic_scans_link_no_link():
    # Arrange
    now = datetime.now(timezone.utc)
    comments = [
        RedditComment(
            body="Great chapter!",
            created_at_timestamp=int(now.timestamp()),
        )
    ]

    # Act
    result = _extract_demonic_scans_link(comments)

    # Assert
    assert result is None


def test_extract_demonic_scans_link_multiple_comments():
    # Arrange
    now = datetime.now(timezone.utc)
    two_days_ago = now - timedelta(days=2)
    comments = [
        RedditComment(
            body="Great chapter!",
            created_at_timestamp=int(now.timestamp()),
        ),
        RedditComment(
            body="Old link: https://demonicscans.org/chapter/old",
            created_at_timestamp=int(two_days_ago.timestamp()),
        ),
        RedditComment(
            body="New link: https://demonicscans.org/chapter/new",
            created_at_timestamp=int(now.timestamp()),
        ),
    ]

    # Act
    result = _extract_demonic_scans_link(comments)

    # Assert
    assert result == "https://demonicscans.org/chapter/new"


def test_extract_demonic_scans_link_case_insensitive():
    # Arrange
    now = datetime.now(timezone.utc)
    comments = [
        RedditComment(
            body="Check out https://DemonicScans.org/chapter/123",
            created_at_timestamp=int(now.timestamp()),
        )
    ]

    # Act
    result = _extract_demonic_scans_link(comments)

    # Assert
    assert result == "https://DemonicScans.org/chapter/123"


def test_extract_demonic_scans_link_with_surrounding_punctuation():
    # Arrange
    now = datetime.now(timezone.utc)
    comments = [
        RedditComment(
            body="Here it is (https://demonicscans.org/chapter/456) enjoy!",
            created_at_timestamp=int(now.timestamp()),
        )
    ]

    # Act
    result = _extract_demonic_scans_link(comments)

    # Assert
    assert result == "https://demonicscans.org/chapter/456"
