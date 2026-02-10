from enum import Enum
from functools import lru_cache
from typing import Type, TypeVar

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic import BaseModel


@lru_cache()
def _get_secret_client() -> SecretClient:
    """Get or create a cached SecretClient instance.

    This significantly reduces Azure Key Vault calls by reusing the same
    client instance across all secret fetches within a function app instance.
    """
    key_vault_url = "https://omlnaut-sebastian.vault.azure.net/"
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=key_vault_url, credential=credential)


class SecretKeys(Enum):
    TelegramSebastianToken = "SebastianTelegramToken"
    GoogleCredentials = "GoogleCredentials"
    MangaUpdateCredentials = "MangaUpdateCredentials"
    RedditCredentials = "RedditCredentials"
    MietplanCredentials = "MietplanCredentials"
    GeminiApiKey = "GeminiApiKey"

    def __str__(self):
        return self.value


T = TypeVar("T", bound=BaseModel)


def get_secret(secret_name: str | SecretKeys, model: Type[T]) -> T:
    """
    Retrieve a secret value from Azure Key Vault and parse it into the provided model type.

    Args:
        secret_name (str | SecretKeys): The name of the secret to retrieve.
        model (Type[T]): The Pydantic model class to parse the secret value into.

    Returns:
        T: An instance of the provided model type parsed from the secret value.

    Raises:
        Exception: If the secret is not found in the Key Vault.

    Note:
        Uses a cached SecretClient to minimize Azure Key Vault operations.
        The cache persists within a function app instance's lifetime.
    """
    secret_client = _get_secret_client()

    if isinstance(secret_name, SecretKeys):
        secret_name = str(secret_name)

    secret_str = secret_client.get_secret(secret_name).value

    if not secret_str:
        raise Exception(f"Secret {secret_name} not found in Key Vault")

    return model.model_validate_json(secret_str)
