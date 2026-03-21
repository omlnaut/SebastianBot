# pyright: standard
from datetime import datetime

from bs4 import BeautifulSoup

from sebastian.clients.bibo.client._models import BookLendingInfoRaw, TimeRange


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str.strip(), "%d.%m.%Y")


def _parse_row(cells: list) -> BookLendingInfoRaw:
    book_id = cells[0].find("input", type="hidden")["value"]
    title = cells[1].find("strong").get_text(strip=True)

    lines = [
        line.strip()
        for line in cells[2].get_text(separator="\n", strip=True).split("\n")
        if line.strip()
    ]
    date_line = next(line for line in lines if " - " in line and line[0].isdigit())
    from_str, to_str = date_line.split(" - ")
    location = lines[-1].split("/")[-1].strip()

    return BookLendingInfoRaw(
        title=title,
        id=book_id,
        location=location,
        lending_timerange=TimeRange(
            from_date=_parse_date(from_str),
            to_date=_parse_date(to_str),
        ),
    )


def parse_account_page(html: str) -> list[BookLendingInfoRaw]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="data")
    return [
        _parse_row(row.find_all("td"))
        for row in table.find_all("tr")  # type: ignore
        if len(row.find_all("td")) >= 3
    ]
