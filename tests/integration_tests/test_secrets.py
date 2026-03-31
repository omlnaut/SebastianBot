import pytest

from cloud.functions.infrastructure.google.credentials import GoogleSecret
from cloud.helper import SecretKeys, get_secret
from sebastian.clients.bibo.credentials import BiboCredentials
from sebastian.clients.google.gemini.credentials import GeminiApiKey
from sebastian.clients.MangaUpdate import MangaUpdateSecret
from sebastian.clients.mietplan.credentials import MietplanCredentials
from sebastian.clients.telegram.config import TelegramConfig


def test_telegram_secret():
    config = get_secret(SecretKeys.TelegramSebastianToken, TelegramConfig)
    assert isinstance(config.token, str)
    assert len(config.token) > 0
    assert isinstance(config.chat_id, int)


def test_google_credentials():
    secret = get_secret(SecretKeys.GoogleCredentials, GoogleSecret)
    assert isinstance(secret.credentials.client_id, str)
    assert len(secret.credentials.client_id) > 0


def test_mangaupdate_credentials():
    credentials = get_secret(SecretKeys.MangaUpdateCredentials, MangaUpdateSecret)
    assert isinstance(credentials.username, str)
    assert len(credentials.username) > 0
    assert isinstance(credentials.password, str)
    assert len(credentials.password) > 0


def test_mietplan_credentials():
    credentials = get_secret(SecretKeys.MietplanCredentials, MietplanCredentials)
    assert isinstance(credentials.username, str)
    assert len(credentials.username) > 0
    assert isinstance(credentials.password, str)
    assert len(credentials.password) > 0


def test_gemini_api_key():
    credentials = get_secret(SecretKeys.GeminiApiKey, GeminiApiKey)
    assert isinstance(credentials.api_key, str)
    assert len(credentials.api_key) > 0


def test_bibo_credentials():
    credentials = get_secret(SecretKeys.BiboCredentials, BiboCredentials)
    assert isinstance(credentials.username, str)
    assert len(credentials.username) > 0
    assert isinstance(credentials.password, str)
    assert len(credentials.password) > 0
