# pyright: standard
import pytest

from cloud.functions.infrastructure.google.credentials import GoogleSecret
from cloud.helper import SecretKeys, get_secret
from sebastian.clients.bibo.credentials import BiboCredentials
from sebastian.clients.google.gemini.credentials import GeminiApiKey
from sebastian.clients.MangaUpdate import MangaUpdateSecret
from sebastian.clients.mietplan.credentials import MietplanCredentials
from sebastian.clients.telegram.config import TelegramConfig


@pytest.mark.parametrize(
    "key,model",
    [
        (SecretKeys.TelegramSebastianToken, TelegramConfig),
        (SecretKeys.GoogleCredentials, GoogleSecret),
        (SecretKeys.MangaUpdateCredentials, MangaUpdateSecret),
        (SecretKeys.MietplanCredentials, MietplanCredentials),
        (SecretKeys.GeminiApiKey, GeminiApiKey),
        (SecretKeys.BiboCredentials, BiboCredentials),
    ],
)
def test_secret_can_be_fetched_and_parsed(key: SecretKeys, model: type) -> None:
    result = get_secret(key, model)
    assert isinstance(result, model)
