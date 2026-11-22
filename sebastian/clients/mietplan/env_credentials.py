import json
import os
from typing import Any, Mapping, cast

from pydantic import ValidationError

from .credentials import MietplanCredentials

ENV_VAR = "SEAMIETPLAN_CREDENTIALS"


class CredentialsError(Exception):
    """The CLI's credentials environment variable is missing or invalid."""


def load_credentials_from_env(
    env: Mapping[str, str] | None = None,
) -> MietplanCredentials:
    """Build the portal credentials from the env var holding their JSON content.

    Accepts both the wrapped Key Vault secret shape (``{"credentials": {...}}``)
    and a bare ``{"username": ..., "password": ...}`` object. The CLI only ever
    reads this variable; nothing is written back to any store.
    """
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
        return MietplanCredentials.model_validate(info)
    except ValidationError as error:
        raise CredentialsError(
            f"{ENV_VAR} is not a valid credentials object: {error}"
        ) from error
