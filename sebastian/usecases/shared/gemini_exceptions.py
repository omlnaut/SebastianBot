from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class GeminiRetryConfiguration:
    retry_horizon: timedelta = timedelta(days=7)
    immediate_retry_delay_seconds: float = 2.0


class TransientGeminiError(Exception):
    """Raised for transient Gemini failures that should be retried later."""


class NonRetryableGeminiError(Exception):
    """Raised for Gemini failures that should not be retried automatically."""
