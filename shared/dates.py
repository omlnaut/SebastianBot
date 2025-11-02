from datetime import datetime
from zoneinfo import ZoneInfo


def get_end_of_day(day: datetime | None = None) -> datetime:
    """
    Returns the end of the given day (23:59:59) in Europe/Berlin timezone.
    If no day is provided, uses the current day.
    """
    tz = ZoneInfo("Europe/Berlin")
    day = day or datetime.now(tz)
    return day.replace(hour=23, minute=59, second=59, microsecond=0)
