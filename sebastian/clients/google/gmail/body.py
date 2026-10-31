from bs4 import BeautifulSoup

from sebastian.domain.gmail import ParsedMail

BODY_FORMAT_TEXT = "text"
BODY_FORMAT_HTML = "html"
BODY_FORMATS = (BODY_FORMAT_TEXT, BODY_FORMAT_HTML)

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


def render_body(parsed: ParsedMail, body_format: str = BODY_FORMAT_TEXT) -> str:
    """Render a body in the requested format.

    ``text`` prefers the plain-text part and converts HTML when there is none, so
    an HTML-only mail is never silently empty. ``html`` returns the raw HTML part
    and falls back to the plain-text body when the mail carries no HTML at all.
    """
    if body_format not in BODY_FORMATS:
        raise ValueError(f"unknown body format: {body_format}")
    if body_format == BODY_FORMAT_HTML:
        return parsed.html_body or parsed.text_body or ""
    return render_text_body(parsed)


def truncate(body: str, max_chars: int) -> tuple[str, bool]:
    """Cut a body to ``max_chars`` and report whether anything was dropped."""
    if len(body) <= max_chars:
        return body, False
    return body[:max_chars], True
