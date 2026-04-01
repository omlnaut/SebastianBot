from functools import lru_cache
from typing import Generic, TypeVar

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic import BaseModel

from cloud.functions.infrastructure.google.credentials import GoogleSecret as _GoogleSecret
from sebastian.clients.bibo.credentials import BiboCredentials as _BiboCredentials
from sebastian.clients.google.gemini.credentials import GeminiApiKey as _GeminiApiKey
from sebastian.clients.MangaUpdate import MangaUpdateSecret as _MangaUpdateSecret
from sebastian.clients.mietplan.credentials import MietplanCredentials as _MietplanCredentials
from sebastian.clients.telegram.config import TelegramConfig as _TelegramConfig


@lru_cache()
def _get_secret_client() -> SecretClient:
    """Get or create a cached SecretClient instance.

    This significantly reduces Azure Key Vault calls by reusing the same
    client instance across all secret fetches within a function app instance.
    """
    # todo: to appsettings
    key_vault_url = "https://omlnaut-sebastian.vault.azure.net/"
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=key_vault_url, credential=credential)


T = TypeVar("T", bound=BaseModel)


class TypedSecretKey(Generic[T]):
    """A typed key for an Azure Key Vault secret that carries its target model type.

    Use the predefined constants in `SecretKeys` instead of constructing this directly.
    """

    def __init__(self, name: str, model: type[T]) -> None:
        self._name = name
        self._model = model

    @property
    def model(self) -> type[T]:
        return self._model

    def __str__(self) -> str:
        return self._name


class SecretKeys:
    TelegramSebastianToken: TypedSecretKey[_TelegramConfig] = TypedSecretKey("SebastianTelegramToken", _TelegramConfig)
    GoogleCredentials: TypedSecretKey[_GoogleSecret] = TypedSecretKey("GoogleCredentials", _GoogleSecret)
    MangaUpdateCredentials: TypedSecretKey[_MangaUpdateSecret] = TypedSecretKey("MangaUpdateCredentials", _MangaUpdateSecret)
    MietplanCredentials: TypedSecretKey[_MietplanCredentials] = TypedSecretKey("MietplanCredentials", _MietplanCredentials)
    GeminiApiKey: TypedSecretKey[_GeminiApiKey] = TypedSecretKey("GeminiApiKey", _GeminiApiKey)
    BiboCredentials: TypedSecretKey[_BiboCredentials] = TypedSecretKey("BiboCredentials", _BiboCredentials)


def get_secret(key: TypedSecretKey[T]) -> T:
    """Retrieve a secret from Azure Key Vault and parse it into the key's model type.

    Args:
        key: A typed secret key constant from `SecretKeys`.

    Returns:
        An instance of the model type associated with the key.

    Raises:
        Exception: If the secret is not found in the Key Vault.
    """
    secret_client = _get_secret_client()
    secret_str = secret_client.get_secret(str(key)).value

    if not secret_str:
        raise Exception(f"Secret {key} not found in Key Vault")

    return key.model.model_validate_json(secret_str)
