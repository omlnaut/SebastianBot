import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_mangaupdate_service
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from cloud.functions.side_effects.shared import send_eventgrid_events
from function_app import app

from .TriggerTimes import TriggerTimes


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

    service = resolve_mangaupdate_service()

    logging.info("Checking for latest manga chapters")
    actor_result = service.get_latest_chapters()

    send_eventgrid_events([AllActorEventGrid.from_application(actor_result)])
