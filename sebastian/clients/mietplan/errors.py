class MietplanError(Exception):
    """Base class for errors raised by the Mietplan client layer."""


class MietplanAuthError(MietplanError):
    """The portal did not accept the login: the session is not authenticated."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class MietplanPathError(MietplanError):
    """A requested path cannot be made safe to write (usage error)."""


class MietplanPathNotFoundError(MietplanError):
    """The requested file is not in the walked tree (api error)."""


class MietplanFolderReadError(MietplanError):
    """A folder that could hold the requested file could not be read (api error)."""


class MietplanDownloadIoError(MietplanError):
    """A download could not be written to the output directory (io error)."""
