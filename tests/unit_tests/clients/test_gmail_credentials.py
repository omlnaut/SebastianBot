import json

import pytest

from sebastian.clients.google.credentials import (
    ENV_VAR,
    CredentialsError,
    load_credentials_from_env,
)


def _bare_credentials(**overrides) -> dict:
    data = {
        "client_id": "client-id",
        "client_secret": "client-secret",
        "refresh_token": "refresh-token",
        "token": "access-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.modify"],
        "universe_domain": "googleapis.com",
        "account": "",
        "expiry": "2026-10-21T20:46:33Z",
    }
    data.update(overrides)
    return data


def test_loader_accepts_the_bare_authorized_user_object():
    credentials = load_credentials_from_env({ENV_VAR: json.dumps(_bare_credentials())})

    assert credentials.client_id == "client-id"
    assert credentials.refresh_token == "refresh-token"


def test_loader_accepts_the_wrapped_secret_shape():
    credentials = load_credentials_from_env(
        {ENV_VAR: json.dumps({"credentials": _bare_credentials()})}
    )

    assert credentials.refresh_token == "refresh-token"


def test_loader_reports_a_missing_variable_by_name():
    with pytest.raises(CredentialsError) as error:
        load_credentials_from_env({})

    assert ENV_VAR in str(error.value)


def test_loader_reports_invalid_json_by_variable_name():
    with pytest.raises(CredentialsError) as error:
        load_credentials_from_env({ENV_VAR: "{not json"})

    assert ENV_VAR in str(error.value)


def test_loader_reports_an_invalid_credentials_object():
    with pytest.raises(CredentialsError) as error:
        load_credentials_from_env({ENV_VAR: json.dumps({"foo": "bar"})})

    assert ENV_VAR in str(error.value)
