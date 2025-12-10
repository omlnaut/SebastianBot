from datetime import datetime, timedelta, timezone

from sebastian.clients.google.gmail.query_builder import GmailQueryBuilder
from sebastian.protocols.gmail import IGmailClient
from sebastian.shared import Result

from .models import PickupData
from .parsing import parse_dhl_pickup_email_html


class DeliveryReadyService:
    def __init__(self, gmail_client: IGmailClient):
        self.gmail_client = gmail_client

    def get_recent_dhl_pickups(self, hours_back: int = 720) -> Result[list[PickupData]]:
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_back)

            query = (
                GmailQueryBuilder()
                .from_email("order-update@amazon.de")
                .subject("Ihr Paket kann bei DHL", exact=True)
                .after_date(time_threshold)
                .build()
            )

            mails = self.gmail_client.fetch_mails(query)

            pickups: list[PickupData] = []
            errors: list[str] = []

            for mail in mails:
                try:
                    pickup_data = parse_dhl_pickup_email_html(mail.payload)
                    pickups.append(pickup_data)
                except Exception as e:
                    errors.append(f"Error parsing email: {str(e)}")

            return Result.from_item(item=pickups, errors=errors)

        except Exception as e:
            raise Exception(f"Failed to fetch DHL pickups: {str(e)}")
