from pathlib import Path

from sebastian.usecases.DeliveryReady.parsing import parse_dhl_pickup_email_html


def test_parsing():
    html = open(Path(__file__).parent / "dhl_test_mail.html", "r").read()
    parsed = parse_dhl_pickup_email_html(html)

    assert parsed.tracking_number == "JJD000390016951668949"
    assert parsed.pickup_location == "Packstation 158, Südhöhe 38"
    assert parsed.due_date == "30.05.2026"
    assert parsed.preview == "WOCVRYY Autositz Organizer..."
