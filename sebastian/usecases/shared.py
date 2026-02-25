from typing import Protocol, TypeVar

from sebastian.protocols.models import AllActor
from sebastian.shared import Result


TInput = TypeVar("TInput")


class UseCaseHandler[TInput](Protocol):
    def handle(self, request: TInput) -> AllActor: ...
