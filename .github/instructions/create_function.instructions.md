# When creating a new cloud function (Azure Functions), follow these instructions:
- put into cloud/functions/ directory as {Name}Function.py
- cloud functions are timer-triggered and orchestrate infrastructure interactions
- when creating a new function:
    1. add trigger time to cloud/functions/TriggerTimes.py (cron format: "min hour day month dayofweek")
    2. if using a client, use resolver from cloud/dependencies/clients.py
    3. if using a service, use resolver from cloud/dependencies/usecases.py
    4. create {Name}Function.py with:
        - @app.timer_trigger decorator with schedule from TriggerTimes, arg_name="mytimer", run_on_startup=False, use_monitor=False
        - service resolution via resolve_{name}_service()
        - error handling with try/except
        - output bindings (@task_output_binding, @telegram_output_binding) for infrastructure actions
        - function signature: def check_{usecase_name}(mytimer: TimerRequest, {outputs}) -> None
        - private helper functions (e.g., _map_to_*, _create_*, _to_*) for mapping domain models to events/messages
    5. import function in function_app.py
- functions should:
    - return None (no return value)
    - use logging for info/errors
    - handle exceptions and send error messages via telegram using telegramOutput.set()
    - check for errors using result.has_errors() and send result.errors_string via telegram
    - map service results to infrastructure events (tasks, telegram messages)
    - pass time span parameters to services as `timedelta` objects (construct with `timedelta(hours=1)` etc.) rather than raw ints
- follow naming: check_{usecase_name} for the function name

## Infrastructure Event Models
- models in cloud/functions/infrastructure/**/models.py represent EventGrid events
- use suffix `*EventGrid` to distinguish from domain models (e.g., `CreateTaskEventGrid`, `SendTelegramMessageEventGrid`)
- these models:
    - inherit from BaseModel (pydantic)
    - have a `to_output()` method that returns `func.EventGridOutputEvent`
    - generate unique event IDs and timestamps
    - serialize to JSON for Azure EventGrid
- this naming convention prevents confusion between domain models and infrastructure event models
