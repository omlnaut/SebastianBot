from datetime import datetime, timedelta, timezone

from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.protocols.gmail import IGmailClient
from sebastian.protocols.gemini import IGeminiClient
from sebastian.shared import Result

from .models import ReturnData
from .parsing import parse_return_email_html


class ReturnTrackerService:
    def __init__(self, gmail_client: IGmailClient, gemini_client: IGeminiClient):
        self.gmail_client = gmail_client
        self.gemini_client = gemini_client

    def get_recent_returns(
        self, time_back: timedelta = timedelta(hours=1)
    ) -> Result[list[ReturnData]]:
        """Fetch recent return emails within the given time delta.

        time_back: timedelta indicating how far back to search (e.g. timedelta(hours=1)).
        """
        try:
            time_threshold = datetime.now(timezone.utc) - time_back

            query = (
                GmailQueryBuilder()
                .from_email("rueckgabe@amazon.de")
                .subject("Ihre Rücksendung von", exact=False)
                .after_date(time_threshold)
                .build()
            )

            mails = self.gmail_client.fetch_mails(query)

            returns: list[ReturnData] = []
            errors: list[str] = []

            for mail in mails:
                result = parse_return_email_html(mail.payload, self.gemini_client)
                if result.item:
                    returns.append(result.item)
                if result.errors:
                    errors.extend(result.errors)

            return Result.from_item(item=returns, errors=errors)
        except Exception as e:
            raise Exception(f"Failed to fetch return emails: {str(e)}")
