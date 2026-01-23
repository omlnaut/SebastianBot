from datetime import datetime
from sebastian.protocols.gmail.IClient import IGmailClient
from sebastian.shared.Result import Result
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.usecases.AllHandler.prompt_builder import clean_html_tags
from sebastian.usecases.AllHandler.prompt_models import AllHandlerEvent
from sebastian.usecases.AllHandler.protocol import IAllHandlerService


class MailToAllHandler:
    def __init__(
        self, mail_client: IGmailClient, all_handler_service: IAllHandlerService
    ):
        self.mail_client = mail_client
        self.all_handler_service = all_handler_service

    def process_recent_emails(self, after: datetime) -> list[Result[AllHandlerEvent]]:
        query = GmailQueryBuilder().after_date(after).exclude_me().build()

        emails = self.mail_client.fetch_mails(query)
        clean_payloads = [clean_html_tags(email.payload) for email in emails]

        events = self.all_handler_service.handle_content(clean_payloads)

        return events
