import requests
from bs4 import BeautifulSoup

LOGIN_CSRF_URL = "https://mietplan-dresden.de/login/"


def _extract_csrf_token(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    input_element = soup.find("input", {"name": "csrf"})
    if input_element is None:
        raise ValueError("No login form found for csrf token")

    csrf_token = input_element.get("value")
    if not csrf_token:
        raise ValueError("Empty CSRF token found in the login form")

    return str(csrf_token)


def _fetch_csrf_token(session: requests.Session) -> str:
    response = session.get(LOGIN_CSRF_URL)
    response.raise_for_status()
    return _extract_csrf_token(response.content.decode(encoding="latin-1"))


def login(session: requests.Session, username: str, password: str) -> None:
    csrf_token = _fetch_csrf_token(session)
    login_url = "https://mietplan-dresden.de/auctores/scs/auctores.controller.web.InfoLoginMultiController"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en-DE;q=0.7,en;q=0.6",
        "Cache-Control": "max-age=0",
        "Origin": "https://mietplan-dresden.de",
        "Referer": "https://mietplan-dresden.de/login/",
        "DNT": "1",
        "Sec-CH-UA": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }

    data = {
        "csrf": csrf_token,
        "fdInf_ID": "CY25277299X1116e405343XY7477",
        "fdCtrlType": "FORWARDER",
        "fdMode": "MODE_LOGIN",
        "dbUserID": username,
        "dbPasswort": password,
    }

    response = session.post(login_url, headers=headers, data=data)
    response.raise_for_status()
