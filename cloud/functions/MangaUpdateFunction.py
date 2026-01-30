import logging

from azure.functions import EventGridOutputEvent, Out, TimerRequest

from cloud.dependencies.usecases import resolve_mangaupdate_service
from cloud.functions.infrastructure.AllActor.helper import all_actor_output_binding
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.MangaUpdate,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
@all_actor_output_binding()
def check_manga_update(
    mytimer: TimerRequest,
    allActorOutput: Out[EventGridOutputEvent],
) -> None:
    logging.info("MangaUpdate timer function processed a request.")

    service = resolve_mangaupdate_service()

    logging.info("Checking for latest manga chapters")
    actor_result = service.get_latest_chapters()

    allActorOutput.set(AllActorEventGrid.from_application(actor_result).to_output())
