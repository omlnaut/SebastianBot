import requests


def download_file_to_ram(session: requests.Session, download_path: str) -> bytes:
    download_base = "https://mietplan-dresden.de"
    download_url = download_base + download_path
    response = session.get(download_url)

    response.raise_for_status()

    return response.content
