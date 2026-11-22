"""The host CLI's Mietplan credentials come from the environment, never a store."""

import json

import pytest

from sebastian.clients.mietplan.credentials import MietplanCredentials
from sebastian.clients.mietplan.env_credentials import (
    ENV_VAR,
    CredentialsError,
    load_credentials_from_env,
)


def test_a_missing_variable_is_a_credentials_error_naming_it():
    with pytest.raises(CredentialsError) as raised:
        load_credentials_from_env({})

    assert ENV_VAR in str(raised.value)


def test_an_empty_variable_is_a_credentials_error_naming_it():
    with pytest.raises(CredentialsError) as raised:
        load_credentials_from_env({ENV_VAR: ""})

    assert ENV_VAR in str(raised.value)


def test_invalid_json_is_a_credentials_error():
    with pytest.raises(CredentialsError) as raised:
        load_credentials_from_env({ENV_VAR: "{not json"})

    assert ENV_VAR in str(raised.value)
    assert "JSON" in str(raised.value)


def test_the_plain_credentials_object_is_accepted():
    raw = {"username": "me@example.com", "password": "geheim"}

    credentials = load_credentials_from_env({ENV_VAR: json.dumps(raw)})

    assert credentials == MietplanCredentials(
        username="me@example.com", password="geheim"
    )


def test_the_wrapped_key_vault_shape_is_not_accepted():
    raw = {"credentials": {"username": "me@example.com", "password": "geheim"}}

    with pytest.raises(CredentialsError) as raised:
        load_credentials_from_env({ENV_VAR: json.dumps(raw)})

    assert ENV_VAR in str(raised.value)


def test_a_credentials_object_without_a_password_is_a_credentials_error():
    raw = {"username": "me@example.com"}

    with pytest.raises(CredentialsError) as raised:
        load_credentials_from_env({ENV_VAR: json.dumps(raw)})

    assert ENV_VAR in str(raised.value)


def test_the_process_environment_is_used_when_no_mapping_is_given(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(ENV_VAR, json.dumps({"username": "u", "password": "p"}))

    assert load_credentials_from_env().username == "u"
