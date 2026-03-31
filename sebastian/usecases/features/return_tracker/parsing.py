from pydantic import BaseModel, Field
from bs4 import BeautifulSoup

from .protocols import GeminiClient


class ReturnData(BaseModel):
    return_date: str = Field(
        description="The date until the return is due. If present, include day month and year."
    )
    order_number: str = Field(description="The order number associated with the return")
    pickup_location: str = Field(
        description="Location where to drop off the return and if i need a printer myself"
    )
    item_title: str = Field(
        description="The title of the item being returned. Might be truncated."
    )


def parse_return_email_html(html: str, gemini_client: GeminiClient) -> ReturnData:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    prompt = f"""Given the following email text, extract all relevant information:
--- email text start ---
{text}
--- email text end ---
"""
    return gemini_client.get_response(prompt, response_schema=ReturnData)
