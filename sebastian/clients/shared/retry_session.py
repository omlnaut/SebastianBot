from collections.abc import Mapping

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_default_headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    )
}


def create_retry_session(
    *,
    total_retries: int = 5,
    connect_retries: int | None = None,
    read_retries: int | None = None,
    status_retries: int | None = None,
    backoff_factor: float = 1.0,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
    allowed_methods: frozenset[str] = frozenset({"GET", "POST"}),
    default_headers: Mapping[str, str] | None = None,
) -> requests.Session:
    session = requests.Session()

    retry = Retry(
        total=total_retries,
        connect=connect_retries if connect_retries is not None else total_retries,
        read=read_retries if read_retries is not None else total_retries,
        status=status_retries if status_retries is not None else total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update(default_headers or _default_headers)

    return session
