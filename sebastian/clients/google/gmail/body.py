from bs4 import BeautifulSoup

from sebastian.domain.gmail import ParsedMail

_BLOCK_TAGS = (
    "p",
    "div",
    "li",
    "tr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "pre",
)


def html_to_text(html: str) -> str:
    """Convert an HTML body to readable plain text."""
    soup = BeautifulSoup(html, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for block in soup.find_all(_BLOCK_TAGS):
        block.append("\n")

    lines = (line.strip() for line in soup.get_text().splitlines())
    return "\n".join(line for line in lines if line)


def render_text_body(parsed: ParsedMail) -> str:
    """Prefer the plain-text body, falling back to converted HTML."""
    if parsed.text_body:
        return parsed.text_body
    if parsed.html_body:
        return html_to_text(parsed.html_body)
    return ""
