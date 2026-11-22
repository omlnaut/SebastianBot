class MietplanError(Exception):
    """Base class for errors raised by the Mietplan client layer."""


class MietplanAuthError(MietplanError):
    """The portal did not accept the login: the session is not authenticated."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status
