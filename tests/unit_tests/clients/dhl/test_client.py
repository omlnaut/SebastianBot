from typing import Any

import pytest
import requests

from sebastian.clients.dhl.client import DhlClient


class _FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._payload


class _InvalidJsonResponse(_FakeResponse):
    def json(self) -> dict[str, Any]:
        raise ValueError("invalid json")


def test_has_packstation_status_returns_true_when_status_contains_packstation(
    monkeypatch: pytest.MonkeyPatch,
):
    client = DhlClient()

    def _fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(
            {
                "sendungen": [
                    {
                        "sendungsdetails": {
                            "sendungsverlauf": {"status": "Abholung aus Packstation"}
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(requests, "get", _fake_get)

    assert client.is_retrieved("00340434684233582597") is True


def test_has_packstation_status_returns_false_when_packstation_is_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    client = DhlClient()

    def _fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(
            {
                "sendungen": [
                    {
                        "sendungsdetails": {
                            "sendungsverlauf": {"status": "In Zustellung"}
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(requests, "get", _fake_get)

    assert client.is_retrieved("00340434684233582597") is False


def test_has_packstation_status_uses_current_status_only(
    monkeypatch: pytest.MonkeyPatch,
):
    client = DhlClient()

    def _fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(
            {
                "sendungen": [
                    {
                        "sendungsdetails": {
                            "sendungsverlauf": {
                                "status": "In Zustellung",
                                "events": [
                                    {
                                        "status": "Die Sendung liegt in der Packstation zur Abholung bereit."
                                    }
                                ],
                            }
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(requests, "get", _fake_get)

    assert client.is_retrieved("00340434684233582597") is False


def test_has_packstation_status_raises_when_shipments_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    client = DhlClient()

    def _fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse({"sendungen": []})

    monkeypatch.setattr(requests, "get", _fake_get)

    with pytest.raises(RuntimeError, match="Failed to parse DHL tracking data"):
        client.is_retrieved("00340434684233582597")


def test_has_packstation_status_raises_when_response_invalid(
    monkeypatch: pytest.MonkeyPatch,
):
    client = DhlClient()

    def _fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse({"invalidField": "value"})

    monkeypatch.setattr(requests, "get", _fake_get)

    with pytest.raises(RuntimeError, match="Failed to parse DHL tracking data"):
        client.is_retrieved("00340434684233582597")


def test_has_packstation_status_raises_when_request_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    client = DhlClient()

    def _fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(requests, "get", _fake_get)

    with pytest.raises(RuntimeError, match="Failed to fetch DHL tracking data"):
        client.is_retrieved("00340434684233582597")


def test_has_packstation_status_raises_when_json_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
):
    client = DhlClient()

    def _fake_get(*args: Any, **kwargs: Any) -> _InvalidJsonResponse:
        return _InvalidJsonResponse({})

    monkeypatch.setattr(requests, "get", _fake_get)

    with pytest.raises(RuntimeError, match="Failed to parse DHL tracking data"):
        client.is_retrieved("00340434684233582597")
