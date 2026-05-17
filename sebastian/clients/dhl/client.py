from __future__ import annotations

import requests
from pydantic import BaseModel, ConfigDict


class _TrackingStatus(BaseModel):
    status: str


class _SendungsDetails(BaseModel):
    sendungsverlauf: _TrackingStatus


class _Sendung(BaseModel):
    sendungsdetails: _SendungsDetails


class _DhlResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    sendungen: list[_Sendung]


class DhlClient:
    _SEARCH_URL = "https://www.dhl.de/int-verfolgen/data/search"
    _USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )

    def is_retrieved(
        self, tracking_number: str, language: str = "de", domain: str = "de"
    ) -> bool:
        try:
            response_data = requests.get(
                self._SEARCH_URL,
                params={
                    "piececode": tracking_number,
                    "noRedirect": "true",
                    "language": language,
                    "lang": language,
                    "domain": domain,
                },
                headers={
                    "accept": "application/json",
                    "user-agent": self._USER_AGENT,
                },
                timeout=30,
            )
            response_data.raise_for_status()
            parsed = _DhlResponse.model_validate(response_data.json())
            current_status = parsed.sendungen[0].sendungsdetails.sendungsverlauf.status
            return "abholung aus packstation" in current_status.lower()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to fetch DHL tracking data for {tracking_number}"
            ) from exc
        except (ValueError, IndexError) as exc:
            raise RuntimeError(
                f"Failed to parse DHL tracking data for {tracking_number}"
            ) from exc
