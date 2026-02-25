from typing import Protocol, TypeVar

from sebastian.shared import Result


TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class UseCaseHandler[TInput, TOutput](Protocol):
    def handle(self, request: TInput) -> Result[TOutput]: ...
