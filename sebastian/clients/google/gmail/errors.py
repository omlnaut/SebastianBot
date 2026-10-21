class GmailError(Exception):
    """Base class for errors raised by the Gmail client layer."""


class GmailApiError(GmailError):
    """A Gmail API call failed."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class GmailAuthError(GmailError):
    """Gmail rejected the credentials or token refresh."""
