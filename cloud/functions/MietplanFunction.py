from datetime import timedelta
import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_mietplan_service
from cloud.functions.infrastructure.AllActor.models import AllActorEventGrid
from cloud.functions.side_effects.shared import send_eventgrid_events
from function_app import app

from .TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.Mietplan,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_mietplan(
    mytimer: TimerRequest,
) -> None:
    logging.info("Checking for new mietplan files")

    service = resolve_mietplan_service()
    actor_result = service.process_new_files(max_file_age=timedelta(days=1))

    send_eventgrid_events([AllActorEventGrid.from_application(actor_result)])
