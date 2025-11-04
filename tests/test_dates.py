from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from shared.dates import get_end_of_day, is_at_most_one_day_old


def test_get_end_of_day_specific_day():
    # Test with a specific day
    day = datetime(2025, 11, 4, 10, 30, tzinfo=ZoneInfo("Europe/Berlin"))
    end_of_day = get_end_of_day(day)
    assert end_of_day == datetime(
        2025, 11, 4, 23, 59, 59, tzinfo=ZoneInfo("Europe/Berlin")
    )


def test_get_end_of_day_current_day():
    # Test with no day provided (current day)
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    end_of_today = get_end_of_day()
    assert end_of_today.date() == now.date()
    assert end_of_today.hour == 23
    assert end_of_today.minute == 59
    assert end_of_today.second == 59


def test_is_at_most_one_day_old_within_one_day():
    # Test with a date within one day
    now = datetime.now(ZoneInfo("UTC"))
    one_day_ago = now - timedelta(hours=23)
    assert is_at_most_one_day_old(one_day_ago) is True


def test_is_at_most_one_day_old_exactly_one_day():
    # Test with a date exactly one day old
    now = datetime.now(ZoneInfo("UTC"))
    exactly_one_day_ago = now - timedelta(days=1)
    assert is_at_most_one_day_old(exactly_one_day_ago) is True


def test_is_at_most_one_day_old_older_than_one_day():
    # Test with a date older than one day
    now = datetime.now(ZoneInfo("UTC"))
    older_than_one_day = now - timedelta(days=2)
    assert is_at_most_one_day_old(older_than_one_day) is False
