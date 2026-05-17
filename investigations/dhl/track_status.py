from __future__ import annotations

import argparse
from typing import Any

import requests

SEARCH_URL = "https://www.dhl.de/int-verfolgen/data/search"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)


def fetch_tracking_data(
    piececode: str, language: str = "de", domain: str = "de"
) -> dict[str, Any]:
    response = requests.get(
        SEARCH_URL,
        params={
            "piececode": piececode,
            "noRedirect": "true",
            "language": language,
            "lang": language,
            "domain": domain,
        },
        headers={
            "accept": "application/json",
            "user-agent": USER_AGENT,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def extract_current_status(payload: dict[str, Any]) -> str:
    shipments = payload.get("sendungen")
    if not shipments:
        raise ValueError("No shipments found in DHL response")

    return shipments[0]["sendungsdetails"]["sendungsverlauf"]["status"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch the current DHL tracking status"
    )
    parser.add_argument("piececode", help="DHL tracking number / piececode")
    parser.add_argument("--language", default="de")
    parser.add_argument("--domain", default="de")
    args = parser.parse_args()

    payload = fetch_tracking_data(
        piececode=args.piececode,
        language=args.language,
        domain=args.domain,
    )
    print(extract_current_status(payload))


if __name__ == "__main__":
    main()
