import requests
from bs4 import BeautifulSoup

BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _fetch_cs_id(session: requests.Session) -> str:
    response = session.get(f"{BASE_URL}/start.do?Login=webopac&BaseURL=this")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cs_id_input = soup.find("input", {"name": "CSId"})
    if cs_id_input is None:
        raise ValueError("CSId field not found in login page")
    return str(cs_id_input["value"])  # type: ignore


def _post_login(
    session: requests.Session, cs_id: str, username: str, password: str
) -> None:
    response = session.post(
        f"{BASE_URL}/login.do",
        data={
            "methodToCall": "submit",
            "CSId": cs_id,
            "username": username,
            "password": password,
        },
    )
    response.raise_for_status()
    if "Abmelden" not in response.text:
        raise ValueError("Login failed — no logout link found in response")


def login(session: requests.Session, username: str, password: str) -> None:
    session.headers.update(_HEADERS)
    cs_id = _fetch_cs_id(session)
    _post_login(session, cs_id, username, password)
