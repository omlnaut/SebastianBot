from datetime import datetime, timedelta, timezone

from sebastian.clients.google.gmail.query_builder import GmailQueryBuilder
from sebastian.protocols.gmail import GmailClientProtocol
from sebastian.shared import Result

from .models import ReturnData
from .parsing import parse_return_email_html


class ReturnTrackerService:
    def __init__(self, gmail_client: GmailClientProtocol):
        self.gmail_client = gmail_client

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
                try:
                    returns.append(parse_return_email_html(mail.payload))
                except Exception as e:  # pragma: no cover - parsing robustness
                    errors.append(f"Error parsing return email: {str(e)}")

            return Result.from_item(item=returns, errors=errors)
        except Exception as e:
            raise Exception(f"Failed to fetch return emails: {str(e)}")
