import logging
from datetime import timedelta

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_mangaupdate_service
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import manga_update

from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.MangaUpdate,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_manga_update(
    mytimer: TimerRequest,
) -> None:
    logging.info("MangaUpdate timer function processed a request.")

    perform_usecase_from_request(
        manga_update.Request(time_back=timedelta(days=1)), resolve_mangaupdate_service
    )
