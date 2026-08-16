from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class MailRetryConfiguration:
    retry_horizon: timedelta = timedelta(days=7)
    immediate_retry_delay_seconds: float = 2.0
