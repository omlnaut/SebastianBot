"""Live-portal fixtures. Dev machine only: no `SEAMIETPLAN_CREDENTIALS`, no tests.

This is the only place `seadepot search` meets the real webdepot. It needs no
Azure login and no Key Vault, just the credentials JSON in the environment.
"""

import os

import pytest

from sebastian.clients.mietplan.client.client import MietplanClient
from sebastian.clients.mietplan.env_credentials import (
    ENV_VAR,
    load_credentials_from_env,
)


@pytest.fixture(scope="session")
def mietplan_client() -> MietplanClient:
    if not os.environ.get(ENV_VAR):
        pytest.skip(f"{ENV_VAR} is not set: live portal tests are dev-machine only")
    return MietplanClient(load_credentials_from_env())
