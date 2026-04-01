# pyright: standard
from typing import Any
import pytest

from cloud.helper import SecretKeys, get_secret
from cloud.helper.secrets import TypedSecretKey


@pytest.mark.parametrize(
    "key",
    [
        SecretKeys.TelegramSebastianToken,
        SecretKeys.GoogleCredentials,
        SecretKeys.MangaUpdateCredentials,
        SecretKeys.MietplanCredentials,
        SecretKeys.GeminiApiKey,
        SecretKeys.BiboCredentials,
    ],
    ids=lambda k: k._name,
)
def test_secret_can_be_fetched_and_parsed(key: TypedSecretKey[Any]) -> None:
    result = get_secret(key)
    assert isinstance(result, key.model)
