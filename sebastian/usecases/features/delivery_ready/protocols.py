from typing import Protocol, TypeVar
from pydantic import BaseModel

from sebastian.domain.gmail import FullMailResponse

__all__ = ["GmailClient", "GeminiClient"]

T = TypeVar("T", bound=BaseModel)


class GeminiClient(Protocol):
    def get_response(self, prompt: str, response_schema: type[T]) -> T: ...


class GmailClient(Protocol):
    def fetch_mails(self, query: str) -> list[FullMailResponse]: ...
