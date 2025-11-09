# When creating a new cloud function (Azure Functions), follow these instructions:
- put into cloud/functions/ directory as {Name}Function.py
- cloud functions are timer-triggered and orchestrate infrastructure interactions
- when creating a new function:
    1. add trigger time to cloud/functions/TriggerTimes.py (cron format: "min hour day month dayofweek")
    2. if using a client, use resolver from cloud/dependencies/clients.py
    3. if using a service, use resolver from cloud/dependencies/services.py
    4. create {Name}Function.py with:
        - @app.timer_trigger decorator with schedule from TriggerTimes
        - service resolution via resolve_{name}_service()
        - error handling with try/except
        - output bindings (@task_output_binding, @telegram_output_binding) for infrastructure actions
        - private helper functions (e.g., _map_to_task_event) for mapping domain models to events
    5. import function in function_app.py
- functions should:
    - use logging for info/errors
    - handle exceptions and send error messages via telegram
    - map service results to infrastructure events (tasks, telegram messages)
- follow naming: check_{usecase_name} for the function name
