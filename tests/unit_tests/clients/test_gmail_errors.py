import json

import pytest
from googleapiclient.errors import HttpError

from sebastian.clients.google.gmail.errors import (
    GmailApiError,
    GmailAuthError,
    gmail_error_from_http,
)


class _Response:
    def __init__(self, status: int, reason: str = "Error") -> None:
        self.status = status
        self.reason = reason


def _http_error(
    status: int, body: dict | None = None, reason: str = "Error"
) -> HttpError:
    content = json.dumps(body).encode("utf-8") if body is not None else b"not json"
    return HttpError(
        _Response(status, reason),
        content,
        uri="https://gmail.googleapis.com/gmail/v1/users/me/messages/0000",
    )


def _not_found_body() -> dict:
    return {
        "error": {
            "code": 404,
            "message": "Requested entity was not found.",
            "errors": [
                {
                    "message": "Requested entity was not found.",
                    "domain": "global",
                    "reason": "notFound",
                }
            ],
        }
    }


def test_a_404_becomes_one_sentence_with_status_and_reason():
    error = gmail_error_from_http(_http_error(404, _not_found_body()))

    assert isinstance(error, GmailApiError)
    assert str(error) == "Requested entity was not found."
    assert (error.status, error.reason) == (404, "notFound")
    assert "gmail.googleapis.com" not in str(error)
    assert "<HttpError" not in str(error)


def test_a_401_becomes_an_auth_error_with_status_and_reason():
    body = {
        "error": {
            "code": 401,
            "message": "Invalid Credentials",
            "errors": [{"message": "Invalid Credentials", "reason": "authError"}],
        }
    }

    error = gmail_error_from_http(_http_error(401, body))

    assert isinstance(error, GmailAuthError)
    assert str(error) == "Invalid Credentials"
    assert (error.status, error.reason) == (401, "authError")


def test_a_403_about_permissions_is_an_auth_error():
    body = {
        "error": {
            "code": 403,
            "message": "Insufficient Permission",
            "errors": [
                {
                    "message": "Insufficient Permission",
                    "reason": "insufficientPermissions",
                }
            ],
        }
    }

    error = gmail_error_from_http(_http_error(403, body))

    assert isinstance(error, GmailAuthError)
    assert (error.status, error.reason) == (403, "insufficientPermissions")


def test_a_403_about_quota_stays_an_api_error():
    body = {
        "error": {
            "code": 403,
            "message": "User-rate limit exceeded.",
            "errors": [{"message": "Rate limit", "reason": "userRateLimitExceeded"}],
        }
    }

    error = gmail_error_from_http(_http_error(403, body))

    assert isinstance(error, GmailApiError)
    assert str(error) == "User-rate limit exceeded."
    assert (error.status, error.reason) == (403, "userRateLimitExceeded")


def test_a_non_json_body_falls_back_to_the_http_reason():
    error = gmail_error_from_http(_http_error(502, None, reason="Bad Gateway"))

    assert isinstance(error, GmailApiError)
    assert str(error) == "Bad Gateway"
    assert (error.status, error.reason) == (502, None)


def test_a_reason_is_taken_from_details_when_errors_is_absent():
    body = {
        "error": {
            "code": 404,
            "message": "Not found.",
            "details": [{"reason": "notFound"}],
        }
    }

    error = gmail_error_from_http(_http_error(404, body))

    assert isinstance(error, GmailApiError)
    assert error.reason == "notFound"


def test_translation_maps_a_socket_error_instead_of_raising_a_name_error():
    from sebastian.clients.google.gmail.client.service_wrapper import _translate_errors

    @_translate_errors
    def explode():
        raise OSError("network down")

    with pytest.raises(GmailApiError, match="network down"):
        explode()
