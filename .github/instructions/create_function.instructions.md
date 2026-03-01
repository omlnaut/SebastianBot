# When creating a new timer triggered cloud function (Azure Functions), follow these instructions:
- put into cloud/functions/ directory as {Name}Function.py
- cloud functions are timer-triggered and orchestrate infrastructure interactions
- when creating a new function:
    1. add trigger time to cloud/functions/TriggerTimes.py (cron format: "min hour day month dayofweek")
    2. if using a client, use resolver from cloud/dependencies/clients.py
    3. if using a service, use resolver from cloud/dependencies/usecases.py
    4. create {Name}Function.py with:
        - @app.timer_trigger decorator with schedule from TriggerTimes, arg_name="mytimer", run_on_startup=False, use_monitor=False
        - service resolution via resolve_{name}_service()
        - import `send_eventgrid_events` from cloud.functions.side_effects.shared
        - function signature: def check_{usecase_name}(mytimer: TimerRequest) -> None
        - call service and send result: `send_eventgrid_events([AllActorEventGrid.from_application(actor_result)])`
        - no try/except needed - error handling is done in service layer (errors returned in `AllActor.send_messages`)
    5. import function in function_app.py
- functions should:
    - return None (no return value)
    - use logging for info messages
    - be thin wrappers: resolve service → call service → send events
    - pass time span parameters to services as `timedelta` objects (construct with `timedelta(hours=1)` etc.) rather than raw ints
- follow naming: check_{usecase_name} for the function name

## AllActor Pattern for Functions
- functions that need to trigger infrastructure actions (tasks, messages) should:
    - import `send_eventgrid_events` from cloud.functions.side_effects.shared
    - call service method that returns `AllActor` type
    - send to EventGrid: `send_eventgrid_events([AllActorEventGrid.from_application(actor_result)])`
- the `all_handler` function handles routing to specific infrastructure handlers
- no error handling needed in function - services handle errors and return them in `AllActor.send_messages`

# When creating event grid triggered functions, follow these instructions:
- same as above but:
    - use @app.event_grid_trigger decorator with arg_name="azeventgrid"
    - parse payload from event grid event with parse_payload(...)
    - use send_eventgrid_events to send response events (no output binding helpers needed)
    - do NOT create output binding helpers

## Infrastructure Event Models
- models in cloud/functions/infrastructure/**/models.py represent EventGrid events
- use suffix `*EventGrid` to distinguish from domain models (e.g., `CreateTaskEventGrid`, `SendTelegramMessageEventGrid`)
- these models:
    - inherit from BaseModel (pydantic)
    - have a `to_output()` method that returns `func.EventGridOutputEvent`
    - generate unique event IDs and timestamps
    - serialize to JSON for Azure EventGrid
- this naming convention prevents confusion between domain models and infrastructure event models
