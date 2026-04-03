# pyright: standard
import re
from datetime import datetime

from bs4 import BeautifulSoup

from sebastian.shared.dates import TimeRange
from sebastian.usecases.features.bibo_lending_sync.protocols import BookLendingInfo


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str.strip(), "%d.%m.%Y")


def _find_dates(row_content: str) -> TimeRange:
    date_regex = re.compile(
        r"(?P<from_date>\d{2}\.\d{2}\.\d{4}) - (?P<to_date>\d{2}\.\d{2}\.\d{4})"
    )
    match = date_regex.search(row_content)
    if not match:
        raise Exception(f"Did not find date information in {row_content}")

    from_str = match.group("from_date")
    to_str = match.group("to_date")

    return TimeRange(
        from_date=_parse_date(from_str),
        to_date=_parse_date(to_str),
    )


def _find_location(date_and_location_cell_content):
    location_regex = re.compile(r"(?P<location>.+), Tel. [\d]+")
    match = location_regex.search(date_and_location_cell_content)
    if not match:
        raise Exception(
            f"Did not find location information in {date_and_location_cell_content}"
        )
    location = match.group("location").strip()
    return location


def _parse_row(cells: list) -> BookLendingInfo:
    book_id = cells[0].find("input", type="hidden")["value"]
    title = cells[1].find("strong").get_text(strip=True)
    date_and_location_cell_content = cells[2].get_text(separator="\n", strip=True)

    location = _find_location(date_and_location_cell_content)
    lending_timerange = _find_dates(date_and_location_cell_content)

    return BookLendingInfo(
        title=title,
        id=book_id,
        location=location,
        lending_timerange=lending_timerange,
    )


def parse_account_page(html: str) -> list[BookLendingInfo]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="data")
    return [
        _parse_row(row.find_all("td"))
        for row in table.find_all("tr")  # type: ignore
        if len(row.find_all("td")) >= 3
    ]
