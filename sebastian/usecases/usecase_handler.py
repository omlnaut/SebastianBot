from abc import ABC, abstractmethod

from sebastian.protocols.models import AllActor


class UseCaseHandler[TRequest](ABC):
    @abstractmethod
    def handle(self, request: TRequest) -> AllActor: ...
