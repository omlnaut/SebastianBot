import pytest

from cloud.dependencies.clients import resolve_gmail_client
from sebastian.clients.google.gmail.client import GmailClient


@pytest.fixture
def gmail_client() -> GmailClient:
    return resolve_gmail_client()
