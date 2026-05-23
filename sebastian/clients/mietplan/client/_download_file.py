import logging

import requests

REQUEST_TIMEOUT_SECONDS = (10, 120)


def download_file_to_ram(session: requests.Session, download_path: str) -> bytes:
    download_base = "https://mietplan-dresden.de"
    download_url = download_base + download_path
    try:
        response = session.get(download_url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException:
        logging.exception(f"Failed to download mietplan file from url={download_url}")
        raise

    response.raise_for_status()

    return response.content
