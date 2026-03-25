from datetime import date

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from .protocols import GeminiClient


class PickupData(BaseModel):
    tracking_number: str = Field(description="The DHL tracking number of the package.")
    pickup_location: str = Field(
        description="When location is Packstation, only include 'Packstation <Number>' as location."
    )
    due_date: date
    item: str = Field(
        description="Description of the item to be picked up, might be truncated",
    )


def parse_dhl_pickup_email_html(html: str, gemini_client: GeminiClient) -> PickupData:
    soup = BeautifulSoup(html, "html.parser")
    text_content = soup.get_text()

    prompt = f"""Given the following email text, extract all relevant information:
--- email text start ---
{text_content}
--- email text end ---
Current year is {date.today().year}
"""
    return gemini_client.get_response(prompt, response_schema=PickupData)
