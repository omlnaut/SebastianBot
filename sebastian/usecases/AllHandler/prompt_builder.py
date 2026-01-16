from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_prompt_template() -> str:
    return (Path(__file__).parent / "prompt.txt").read_text()


def build_prompt(content: str) -> str:
    template = _load_prompt_template()
    prompt = template.replace("{content}", content)

    return prompt


def clean_html_tags(html_content: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text()
    return text
