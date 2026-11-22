"""Live-only fixtures for the mietplan Drive work.

These tests talk to the real Google Drive and are dev-machine only: they need
the Key Vault / Google credentials the bot uses. On a machine without them the
fixture skips instead of failing.

They only ever create and update (the code under test never deletes, D13), so
every run leaves a ``sebastianbot-integration-<uuid>`` folder behind in the
Drive root. Clean those up by hand if the clutter bothers you.
"""

import pytest

from cloud.dependencies.clients import resolve_google_drive_client
from sebastian.clients.google.drive.client import GoogleDriveClient


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
