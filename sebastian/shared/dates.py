from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def get_end_of_day(day: datetime | None = None) -> datetime:
    """
    Returns the end of the given day (23:59:59) in Europe/Berlin timezone.
    If no day is provided, uses the current day.
    """
    tz = ZoneInfo("Europe/Berlin")
    day = day or datetime.now(tz)
    return day.replace(hour=23, minute=59, second=59, microsecond=0)


def is_at_most_one_day_old(input_date: datetime | date) -> bool:
    """Check if the given date is at most one day old."""
    if isinstance(input_date, datetime):
        input_date = input_date.date()
    now = date.today()
    one_day_ago = now - timedelta(days=1)
    return one_day_ago <= input_date <= now


def to_timestamp(date: datetime | int) -> int:
    """
    Convert a datetime or timestamp to an integer timestamp.
    If a datetime is provided, converts it to a Unix timestamp.
    If an int is provided, returns it as-is.
    """
    if isinstance(date, datetime):
        return int(date.timestamp())
    else:
        return int(date)
