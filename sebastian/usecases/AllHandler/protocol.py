from datetime import datetime
from typing import Protocol

from sebastian.shared.Result import Result
from sebastian.usecases.AllHandler.prompt_models import AllHandlerEvent


class IAllHandlerService(Protocol):
    def handle_content(self, contents: list[str]) -> list[Result[AllHandlerEvent]]: ...
