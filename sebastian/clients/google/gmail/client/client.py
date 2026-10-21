from google.oauth2.credentials import Credentials

from sebastian.clients.google.gmail.parsing import normalize_hit
from sebastian.domain.gmail import (
    FullMailResponse,
    GmailLabel,
    GmailLabelResponse,
    Label,
    PdfAttachment,
    SearchPage,
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
        label_names = {label.id: label.name for label in self.labels()}
        hits = [
            normalize_hit(self._service.fetch_search_message(message_id), label_names)
            for message_id in page.ids
        ]
        return SearchPage(
            hits=hits,
            next_page_token=page.next_page_token,
            result_size_estimate=page.result_size_estimate,
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
