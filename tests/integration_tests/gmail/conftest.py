import pytest

from cloud.dependencies.clients import resolve_gmail_client
from sebastian.protocols.gmail.IClient import IGmailClient


@pytest.fixture
def gmail_client() -> IGmailClient:
    return resolve_gmail_client()
