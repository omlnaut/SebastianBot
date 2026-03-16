from abc import ABC, abstractmethod

from sebastian.protocols.models import AllActor


class UseCaseHandler[TRequest](ABC):
    @abstractmethod
    def handle(self, request: TRequest) -> AllActor: ...

    def name(self) -> str:
        cls = type(self)
        module_name = cls.__module__.replace("sebastian.usecases.", "")
        return module_name
