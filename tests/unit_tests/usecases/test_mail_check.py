from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sebastian.domain.gmail import FullMailResponse, GmailLabel
from sebastian.domain.side_effect import SendMessage, SideEffect
from sebastian.usecases.features.mail_check.handler import Handler, Request


def _mail(mail_id: str, label_ids: list[str] | None = None) -> FullMailResponse:
    labels = label_ids or [GmailLabel.Unread.value]
    internal_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    return FullMailResponse(
        id=mail_id,
        threadId=f"thread-{mail_id}",
        labelIds=labels,
        is_read=False,
        snippet="snippet",
        sizeEstimate=123,
        historyId=f"hist-{mail_id}",
        internalDate=str(internal_ms),
        content="content",
        pdf_parts=[],
    )


class _FakeGmailClient:
    def __init__(self, mails: list[FullMailResponse]):
        self._mails = mails
        self.last_query: str | None = None

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        self.last_query = query
        return self._mails


class _FakeSubUseCase:
    def __init__(
        self,
        name: str,
        should_match: dict[str, bool],
        effects_by_mail: dict[str, list[SideEffect]],
    ):
        self.name = name
        self._should_match = should_match
        self._effects_by_mail = effects_by_mail
        self.checked_mail_ids: list[str] = []
        self.handled_mail_ids: list[str] = []

    def check_if_mail_matches(self, mail: FullMailResponse) -> bool:
        self.checked_mail_ids.append(mail.id)
        return self._should_match.get(mail.id, False)

    def handle_mail(self, mail: FullMailResponse) -> Sequence[SideEffect]:
        self.handled_mail_ids.append(mail.id)
        return self._effects_by_mail.get(mail.id, [])


def test_mail_check_skips_processed_mails():
    processed_mail = _mail("mail-processed", [GmailLabel.Processed.value])
    unprocessed_mail = _mail("mail-unprocessed")
    gmail_client = _FakeGmailClient([processed_mail, unprocessed_mail])

    sub_usecase = _FakeSubUseCase(
        name="sub-a",
        should_match={"mail-unprocessed": True, "mail-processed": True},
        effects_by_mail={"mail-unprocessed": [SendMessage(message="handled")]} ,
    )

    result = Handler(gmail_client=gmail_client, sub_usecases=[sub_usecase]).handle(
        Request(cutoff_date=datetime(2026, 1, 1, tzinfo=timezone.utc))
    )

    assert gmail_client.last_query is not None
    assert "after:" in gmail_client.last_query
    assert sub_usecase.checked_mail_ids == ["mail-unprocessed"]
    assert sub_usecase.handled_mail_ids == ["mail-unprocessed"]
    assert [e.message for e in result if isinstance(e, SendMessage)] == ["handled"]


def test_mail_check_executes_all_matching_sub_usecases_for_same_mail():
    mail = _mail("mail-1")
    gmail_client = _FakeGmailClient([mail])

    sub_a = _FakeSubUseCase(
        name="sub-a",
        should_match={"mail-1": True},
        effects_by_mail={"mail-1": [SendMessage(message="a")]},
    )
    sub_b = _FakeSubUseCase(
        name="sub-b",
        should_match={"mail-1": True},
        effects_by_mail={"mail-1": [SendMessage(message="b")]},
    )

    result = Handler(gmail_client=gmail_client, sub_usecases=[sub_a, sub_b]).handle(
        Request(cutoff_date=datetime(2026, 1, 1, tzinfo=timezone.utc))
    )

    assert sub_a.handled_mail_ids == ["mail-1"]
    assert sub_b.handled_mail_ids == ["mail-1"]
    assert [e.message for e in result if isinstance(e, SendMessage)] == ["a", "b"]


def test_mail_check_returns_no_effects_when_no_sub_usecase_matches():
    mail = _mail("mail-1")
    gmail_client = _FakeGmailClient([mail])

    sub_usecase = _FakeSubUseCase(
        name="sub-a",
        should_match={"mail-1": False},
        effects_by_mail={"mail-1": [SendMessage(message="should-not-run")]},
    )

    result = Handler(gmail_client=gmail_client, sub_usecases=[sub_usecase]).handle(
        Request(cutoff_date=datetime(2026, 1, 1, tzinfo=timezone.utc))
    )

    assert sub_usecase.handled_mail_ids == []
    assert result == []


def test_mail_check_side_effect_order_is_deterministic():
    first_mail = _mail("mail-1")
    second_mail = _mail("mail-2")
    gmail_client = _FakeGmailClient([first_mail, second_mail])

    sub_a = _FakeSubUseCase(
        name="sub-a",
        should_match={"mail-1": True, "mail-2": True},
        effects_by_mail={
            "mail-1": [SendMessage(message="mail-1/a")],
            "mail-2": [SendMessage(message="mail-2/a")],
        },
    )
    sub_b = _FakeSubUseCase(
        name="sub-b",
        should_match={"mail-1": True, "mail-2": True},
        effects_by_mail={
            "mail-1": [SendMessage(message="mail-1/b")],
            "mail-2": [SendMessage(message="mail-2/b")],
        },
    )

    result = Handler(gmail_client=gmail_client, sub_usecases=[sub_a, sub_b]).handle(
        Request(cutoff_date=datetime(2026, 1, 1, tzinfo=timezone.utc))
    )

    assert [e.message for e in result if isinstance(e, SendMessage)] == [
        "mail-1/a",
        "mail-1/b",
        "mail-2/a",
        "mail-2/b",
    ]
