"""A shared fake portal session for the Mietplan client tests.

Requests are matched by what they ask for (folder list vs file list) and which
folder they ask about, so tests describe the tree instead of the URLs.
"""

from typing import Any, Mapping

import requests

TOP = "ac4do35ktgfi79j8ids35om8udm"


class _Response:
    def __init__(
        self,
        payload: Any = None,
        status_code: int = 200,
        text: str = "",
    ):
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)

    def json(self) -> Any:
        if self._payload is None:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self._payload


def folders(*entries: tuple[str, str]) -> _Response:
    """A getFolders answer: (name, folder_id) pairs."""
    return _Response(
        {
            str(index): {
                "filename": name,
                "fileid": folder_id,
                "filechildren": True,
            }
            for index, (name, folder_id) in enumerate(entries)
        }
    )


def files(*entries: tuple[str, str]) -> _Response:
    """A getFiles answer: (portal_creation_date, filepath) pairs."""
    return _Response(
        {
            str(index): {"filecrea": created, "filepath": path}
            for index, (created, path) in enumerate(entries)
        }
    )


def empty() -> _Response:
    return _Response({})


def not_json(
    text: str = "<html><body>Please log in</body></html>",
    status_code: int = 200,
) -> _Response:
    """A portal answer that is HTML rather than the JSON tree."""
    return _Response(text=text, status_code=status_code)


class FakeSession:
    """Stands in for `requests.Session`; responses are keyed by (kind, folder)."""

    def __init__(self, responses: Mapping[tuple[str, str], _Response | Exception]):
        self._responses = dict(responses)
        self.requests: list[tuple[str, str]] = []

    def get(self, url: str, timeout: object = None) -> _Response:
        assert timeout is not None, "every portal request needs a timeout"
        kind = "folders" if "msg=getFolders" in url else "files"
        folder_id = url.split("fdFolder=", 1)[1]
        self.requests.append((kind, folder_id))
        outcome = self._responses.get((kind, folder_id))
        if outcome is None:
            raise AssertionError(f"unexpected portal request: {kind} {folder_id}")
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
