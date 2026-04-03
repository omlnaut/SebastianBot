from abc import ABC, abstractmethod
from typing import Sequence

from sebastian.protocols.models import BaseActorEvent


class UseCaseHandler[TRequest](ABC):
    @abstractmethod
    def handle(self, request: TRequest) -> Sequence[BaseActorEvent]: ...

    def name(self) -> str:
        cls = type(self)
        module_name = cls.__module__.replace("sebastian.usecases.", "")
        return module_name
