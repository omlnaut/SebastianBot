import logging
import os
from datetime import datetime, timezone

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_mail_check
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import mail_check

from ..TriggerTimes import TriggerTimes

_DEFAULT_CUTOFF_DATE = datetime(2026, 8, 5, tzinfo=timezone.utc)


def _resolve_cutoff_date() -> datetime:
    raw_value = os.getenv("MAIL_CHECK_CUTOFF_DATE")
    if not raw_value:
        return _DEFAULT_CUTOFF_DATE

    normalized_value = raw_value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized_value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


@app.timer_trigger(
    schedule=TriggerTimes.MailCheck,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_mail_check(mytimer: TimerRequest) -> None:
    cutoff_date = _resolve_cutoff_date()
    logging.info(
        f"MailCheck timer function processed a request. cutoff_date={cutoff_date.isoformat()}"
    )
    perform_usecase_from_request(
        mail_check.Request(cutoff_date=cutoff_date),
        resolve_mail_check,
    )
