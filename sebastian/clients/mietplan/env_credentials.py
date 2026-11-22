import json
import os
from typing import Mapping

from pydantic import ValidationError

from .credentials import MietplanCredentials

ENV_VAR = "SEAMIETPLAN_CREDENTIALS"


class CredentialsError(Exception):
    """The CLI's credentials environment variable is missing or invalid."""


def load_credentials_from_env(
    env: Mapping[str, str] | None = None,
) -> MietplanCredentials:
    """Build the portal credentials from the env var holding their JSON content.

    The content is the bare ``{"username": ..., "password": ...}`` object (D4);
    the CLI only ever reads this variable and never writes it back anywhere.
    """
    source = os.environ if env is None else env
    raw = source.get(ENV_VAR)
    if not raw:
        raise CredentialsError(f"{ENV_VAR} is not set")

    try:
        data: object = json.loads(raw)
    except json.JSONDecodeError as error:
        raise CredentialsError(f"{ENV_VAR} is not valid JSON: {error}") from error

    try:
        return MietplanCredentials.model_validate(data)
    except ValidationError as error:
        raise CredentialsError(
            f"{ENV_VAR} is not a valid credentials object: {error}"
        ) from error
