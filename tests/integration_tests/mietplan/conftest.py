"""Live fixtures for the mietplan work: the real webdepot and real Google Drive.

Every test in this directory is dev-machine only. Each fixture skips instead of
failing when its credentials are missing, so a bare checkout collects the tests
and reports them as skipped.

* ``mietplan_client`` needs no Azure login and no Key Vault, just the
  credentials JSON in ``SEAMIETPLAN_CREDENTIALS``.
* ``drive_client`` needs the Key Vault / Google credentials the bot uses.

The Drive tests only ever create and update (the code under test never deletes,
D13), so every run leaves a ``sebastianbot-integration-<uuid>`` folder behind in
the Drive root. Clean those up by hand if the clutter bothers you.
"""

import os

import pytest

from cloud.dependencies.clients import resolve_google_drive_client
from sebastian.clients.google.drive.client import GoogleDriveClient
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


@pytest.fixture(scope="module")
def drive_client() -> GoogleDriveClient:
    try:
        client = resolve_google_drive_client()
        # build() does not touch the network; this does, so an invalid token
        # skips here instead of failing the test with an auth error.
        client._service.about().get(fields="user").execute()  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    except Exception as error:  # noqa: BLE001 - any credential failure means "skip"
        pytest.skip(
            f"Google Drive credentials unavailable "
            f"({type(error).__name__}: {error})"
        )
    return client
