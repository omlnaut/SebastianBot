from typing import TypeVar

from pydantic import BaseModel

from sebastian.domain.gmail import FullMailResponse
from pathlib import Path

from sebastian.usecases.features.mail_check import MailRetryConfiguration


def _load_mail() -> FullMailResponse:
    return FullMailResponse.model_validate_json(
        (Path(__file__).parent / "matching_mail.json").read_text()
    )


T = TypeVar("T", bound=BaseModel)


class GeminiClientMock:
    def get_response(self, prompt: str, response_schema: type[T]) -> T: ...


def test_mail_matches() -> None:
    # to be implemented
    from sebastian.usecases.features.return_tracker.handler import MailSubUseCase

    mail = _load_mail()
    usecase = MailSubUseCase(
        retry_configuration=MailRetryConfiguration(),
        llm_client_resolver=lambda: GeminiClientMock(),
    )
    assert usecase.check_if_mail_matches(mail)
