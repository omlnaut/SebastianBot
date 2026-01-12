from datetime import datetime
from sebastian.protocols.gemini.IClient import IGeminiClient
from sebastian.protocols.gmail.IClient import IGmailClient
from sebastian.protocols.gmail.models import FullMailResponse
from sebastian.shared import Result
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.usecases.AllHandler.prompt_builder import build_prompt, clean_html_tags
from sebastian.usecases.AllHandler.prompt_models import AllHandlerEvent


class AllHandlerService:
    # todo: needs to be split into actual AllHandler and "MailToAllHandler"
    def __init__(self, gmail: IGmailClient, gemini: IGeminiClient):
        self.gmail = gmail
        self.gemini = gemini

    def process_all_emails(self, after: datetime) -> list[Result[AllHandlerEvent]]:
        query = GmailQueryBuilder().after_date(after).exclude_me().build()

        emails = self.gmail.fetch_mails(query)

        events = self._process_emails(emails)

        return events

    def _process_emails(
        self, emails: list[FullMailResponse]
    ) -> list[Result[AllHandlerEvent]]:
        events = []
        for email in emails:
            clean_payload = clean_html_tags(email.payload)
            prompt = build_prompt(clean_payload)
            result = self.gemini.get_response(prompt, AllHandlerEvent)
            events.append(result)
        return events
