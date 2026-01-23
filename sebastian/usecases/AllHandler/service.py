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

    def handle_content(self, contents: list[str]) -> list[Result[AllHandlerEvent]]:
        results = []
        for content in contents:
            prompt = build_prompt(clean_html_tags(content))
            result = self.gemini.get_response(prompt, AllHandlerEvent)
            results.append(result)
        return results
