import logging

import requests

from ..errors import MietplanAuthError
from ._walk_from_top_folder import REQUEST_TIMEOUT_SECONDS, folders_url

# The portal answers an unauthenticated folder request with 403 (see V1 in the
# recon note); a login page instead of JSON is the other shape of the same thing.
_AUTH_REJECTED_STATUSES = frozenset({401, 403})


def verify_session(session: requests.Session, folder_id: str) -> None:
    """Prove the session can read the tree, so a rejected login cannot look empty.

    Raises `MietplanAuthError` when the portal says the caller is not logged in.
    Any other failure (connectivity, 5xx) propagates unchanged: it is a portal
    problem, not an auth problem, and the CLI reports it as an api error.
    """
    logging.info(f"Verifying the session against folder {folder_id}")
    try:
        response = session.get(
            folders_url(folder_id), timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.RequestException:
        logging.exception("Session probe failed at the transport level")
        raise
    if response.status_code in _AUTH_REJECTED_STATUSES:
        raise MietplanAuthError(
            f"login was rejected: the portal answered HTTP {response.status_code} "
            f"for folder {folder_id}",
            status=response.status_code,
        )
    response.raise_for_status()
    if not _is_json_object(response):
        raise MietplanAuthError(
            f"login was not accepted: the portal answered folder {folder_id} with "
            "something that is not JSON (a login page, not the file tree)"
        )


def _is_json_object(response: requests.Response) -> bool:
    try:
        payload: object = response.json()
    except ValueError:
        return False
    return isinstance(payload, dict)
