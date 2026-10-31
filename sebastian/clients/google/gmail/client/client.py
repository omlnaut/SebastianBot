from typing import Any

from google.oauth2.credentials import Credentials

from sebastian.clients.google.gmail.attachments import write_attachments
from sebastian.clients.google.gmail.body import render_body, truncate
from sebastian.clients.google.gmail.parsing import normalize_hit, parse_payload
from sebastian.domain.gmail import (
    ComposedDraft,
    CreatedDraft,
    FullMailResponse,
    GmailLabel,
    GmailLabelResponse,
    Label,
    PdfAttachment,
    ReplyContext,
    SearchPage,
    ShownMail,
    WrittenAttachment,
)

from .download_pdf_attachments import download_pdf_attachments_from_messages
from .modify_labels import modify_labels
from .service_wrapper import GmailServiceWrapper


class GmailClient:
    def __init__(self, credentials: Credentials):
        self._service = GmailServiceWrapper(credentials)

    def fetch_mails(self, query: str) -> list[FullMailResponse]:
        """Fetch full emails matching the query. Use GmailQueryBuilder from `sebastian.usecases.shared.query_builder` to build the query."""
        message_ids = self._service.fetch_message_ids(query)
        emails = [self._service.fetch_full_mail(msg_id.id) for msg_id in message_ids]
        return emails

    def download_pdf_attachments(self, mail: FullMailResponse) -> list[PdfAttachment]:
        """Download PDF attachments from a full email message."""
        return download_pdf_attachments_from_messages(self._service, mail)

    def modify_labels(
        self,
        email_id: str,
        add_labels: list[GmailLabel] | None = None,
        remove_labels: list[GmailLabel] | None = None,
    ) -> None:
        """Modify labels on an email by adding and/or removing tags."""
        return modify_labels(
            self._service,
            email_id=email_id,
            add_labels=add_labels,
            remove_labels=remove_labels,
        )

    def get_labels(self) -> list[GmailLabelResponse]:
        """Fetch all labels available in the authenticated Gmail account."""
        return self._service.fetch_labels()

    def search(
        self, query: str, limit: int, page_token: str | None = None
    ) -> SearchPage:
        """Search mail with a raw Gmail query, returning cheap metadata hits."""
        page = self._service.list_message_ids(query, limit, page_token)
        label_names = self._label_names()
        hits = [
            normalize_hit(self._service.fetch_search_message(message_id), label_names)
            for message_id in page.ids
        ]
        return SearchPage(
            hits=hits,
            next_page_token=page.next_page_token,
            result_size_estimate=page.result_size_estimate,
        )

    def show(self, message_id: str, body_format: str, max_chars: int) -> ShownMail:
        """Read one mail in full through the shared parser and hit normalization."""
        message = self._service.fetch_full_message(message_id)
        parsed = parse_payload(message.get("payload") or {})
        body, truncated = truncate(render_body(parsed, body_format), max_chars)
        return ShownMail(
            hit=normalize_hit(message, self._label_names()),
            body=body,
            body_format=body_format,
            truncated=truncated,
        )

    def _label_names(self) -> dict[str, str]:
        return {label.id: label.name for label in self.labels()}

    def save_attachments(
        self, message_id: str, out_dir: str, force: bool
    ) -> list[WrittenAttachment]:
        """Write one mail's attachments into ``out_dir``, fetching content now."""
        message = self._service.fetch_full_message(message_id)
        parsed = parse_payload(message.get("payload") or {})
        return write_attachments(
            parsed.attachments,
            out_dir,
            force,
            fetch=lambda attachment_id: self._service.fetch_attachment(
                message_id, attachment_id
            ),
        )

    def labels(self) -> list[Label]:
        """List labels with ids resolved to readable names."""
        return [
            Label(
                id=label.id,
                name=label.name,
                type=label.type,
                visibility=label.label_list_visibility,
            )
            for label in self._service.list_labels()
        ]

    def own_address(self) -> str:
        """The authenticated account's address, so reply-all can exclude it."""
        return self._service.fetch_profile_address()

    def reply_context(self, message_id: str) -> ReplyContext:
        """Read the headers a reply draft is derived from, without the body."""
        message = self._service.fetch_reply_context(message_id)
        parsed = parse_payload(message.get("payload") or {})
        return ReplyContext(
            thread_id=message.get("threadId") or "",
            sender=parsed.sender,
            to=parsed.to,
            cc=parsed.cc,
            subject=parsed.subject,
            message_id_header=parsed.message_id,
            references=parsed.references,
        )

    def create_draft(self, draft: ComposedDraft) -> CreatedDraft:
        """Create one Gmail draft. This is the only write the CLI performs."""
        message: dict[str, Any] = {"raw": draft.encoded}
        if draft.request.thread_id:
            message["threadId"] = draft.request.thread_id
        response = self._service.create_draft(message)
        created = response.get("message") or {}
        return CreatedDraft(
            draft_id=response["id"],
            message_id=created["id"],
            thread_id=created.get("threadId") or draft.request.thread_id or "",
        )
