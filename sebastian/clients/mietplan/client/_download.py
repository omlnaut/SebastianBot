from io import BytesIO
import requests


def download_file_to_ram(session: requests.Session, download_path: str) -> BytesIO:
    download_base = "https://mietplan-dresden.de"
    download_url = download_base + download_path
    response = session.get(download_url)

    response.raise_for_status()

    file_in_memory = BytesIO(response.content)
    return file_in_memory
