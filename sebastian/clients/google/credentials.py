import json
import os
from typing import Any, Callable, List, Mapping, cast

from pydantic import BaseModel


class Credentials(BaseModel):
    token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: List[str]
    universe_domain: str
    account: str
    expiry: str


class GoogleSecret(BaseModel):
    credentials: Credentials


ENV_VAR = "SEAMAIL_GOOGLE_CREDENTIALS"


class CredentialsError(Exception):
    """The CLI's credentials environment variable is missing or invalid."""


def load_credentials_from_env(env: Mapping[str, str] | None = None):
    """Build Google credentials from the env var holding the credentials JSON.

    Accepts both the wrapped Key Vault secret shape (``{"credentials": {...}}``)
    and a bare authorized-user object. Refresh happens in-process from the stored
    refresh token with no write-back to any store.
    """
    from google.oauth2.credentials import Credentials as GoogleCredentials

    source = os.environ if env is None else env
    raw = source.get(ENV_VAR)
    if not raw:
        raise CredentialsError(f"{ENV_VAR} is not set")

    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as error:
        raise CredentialsError(f"{ENV_VAR} is not valid JSON: {error}") from error

    info: Any = data
    if isinstance(data, dict):
        info = cast(dict[str, Any], data).get("credentials", data)
    try:
        loader = cast(
            Callable[[dict[str, Any]], GoogleCredentials],
            GoogleCredentials.from_authorized_user_info,  # pyright: ignore[reportUnknownMemberType]
        )
        return loader(info)
    except (TypeError, ValueError) as error:
        raise CredentialsError(
            f"{ENV_VAR} is not a valid credentials object: {error}"
        ) from error
