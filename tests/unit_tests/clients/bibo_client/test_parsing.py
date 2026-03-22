from datetime import datetime
from pathlib import Path

from sebastian.clients.bibo.client._models import BookLendingInfo, TimeRange
from sebastian.clients.bibo.client._parse_account_page import parse_account_page


def test_account_page_parsing():
    html = open(Path(__file__).parent / "account_page.html", "r").read()

    parsed = parse_account_page(html)

    assert len(parsed) == 6

    timerange = TimeRange(from_date=datetime(2026, 3, 4), to_date=datetime(2026, 5, 4))

    assert parsed[0] == BookLendingInfo(
        title="Fünf kunterbunte Osterküken",
        id="025391872",
        location="Zentralbibliothek",
        lending_timerange=timerange,
    )
    assert parsed[1] == BookLendingInfo(
        title="Im Osterhasendorf",
        id="014437370",
        location="Zentralbibliothek",
        lending_timerange=timerange,
    )
    assert parsed[2] == BookLendingInfo(
        title="Karlchen und der Kapuzen-Klub",
        id="03782703X",
        location="Zentralbibliothek",
        lending_timerange=timerange,
    )
    assert parsed[3] == BookLendingInfo(
        title="Mein liebstes Osterbuch",
        id="039615269",
        location="Zentralbibliothek",
        lending_timerange=timerange,
    )
    assert parsed[4] == BookLendingInfo(
        title="Ostern mit Familie Hase",
        id="037378324",
        location="Zentralbibliothek",
        lending_timerange=timerange,
    )
    assert parsed[5] == BookLendingInfo(
        title="Wo ist das Osterei versteckt?",
        id="036266616",
        location="Zentralbibliothek",
        lending_timerange=timerange,
    )
