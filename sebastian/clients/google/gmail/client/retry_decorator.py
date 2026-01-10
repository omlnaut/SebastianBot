import logging
import ssl
import socket
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
)
from googleapiclient.errors import HttpError


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if exception is retryable"""
    # Retry network and SSL errors
    if isinstance(exception, (ssl.SSLError, socket.error, ConnectionError, OSError)):
        return True

    # Retry HTTP 5xx server errors, but not 4xx client errors
    if isinstance(exception, HttpError):
        return exception.resp.status >= 500

    return False


def retry_on_network_error(
    max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0
):
    """
    Decorator that retries a function on network and SSL errors using tenacity.

    Handles:
    - SSL errors (including EOF in violation of protocol)
    - Socket errors
    - Connection errors
    - Transient HTTP errors (5xx)

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
    """
    return retry(
        stop=stop_after_attempt(max_retries + 1),
        wait=wait_exponential(
            multiplier=initial_delay, min=initial_delay, max=60, exp_base=backoff_factor
        ),
        retry=retry_if_exception(_is_retryable_error),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    )
