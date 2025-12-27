from bs4 import BeautifulSoup

from sebastian.protocols.gemini import IGeminiClient
from sebastian.shared.Result import Result

from .models import ReturnData


def parse_return_email_html(
    html: str, gemini_client: IGeminiClient
) -> Result[ReturnData]:
    """Parse return email HTML using Gemini to extract structured data.

    Args:
        html: The HTML content of the return email
        gemini_client: Gemini client for AI-powered parsing

    Returns:
        Result containing parsed ReturnData or error messages
    """
    # Extract visible text from HTML
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    # Create prompt for Gemini
    prompt = f"""Given the following email text, extract all relevant information:
--- email text start ---
{text}
--- email text end ---
"""

    # Use Gemini to parse the email
    return gemini_client.get_response(prompt, response_schema=ReturnData)
