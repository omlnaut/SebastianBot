# When creating a new service (usecase), follow these instructions:
- put into usecases dir, each usecase in its own folder
- create a service.py file containing the service class
- services orchestrate clients and business logic
- services should:
    - accept clients via dependency injection in __init__, using protocol types from sebastian/protocols/
    - return `AllActor` for operations that need to interact with infrastructure (create tasks, send messages)
        - return errors in `AllActor.send_messages` list (wrapped in `SendMessage` objects)
        - use try/except at the service layer (not in functions) to catch errors and convert to `SendMessage`
    - return plain types (list, objects) for pure data operations
    - extract domain models in a models.py (pydantic models if parsing is involved, dataclasses otherwise)
    - extract parsing/transformation/logic into separate files if complex
- services must not depend on cloud/infrastructure layer (Azure functions, etc.)
- follow naming convention: {UseCase}Service (e.g., DeliveryReadyService, MangaUpdateService)
- when creating from a notebook: add a section that showcases the usage of the service
- add service resolver in cloud/dependencies/usecases.py (injecting required clients)
- when creating a new service, also create a notebook showcasing the usage. if a notebook alreaddy exists for the service, add to that one instead
- make configuration values, such as time-based thresholds, parameters to the public methods
    - use `timedelta` for any time span arguments (e.g. instead of `hours_back: int`, prefer `time_back: timedelta`)

## Error Handling Strategy
- services should handle errors and return them in the `AllActor` response:
    - wrap try/except blocks around client calls that might fail
    - convert exceptions to `SendMessage` objects in `AllActor.send_messages` list
    - keep try/except blocks as low as possible (around specific operations, not entire methods)
    - successful operations should be returned in `AllActor.create_tasks` or other appropriate fields
- Azure functions should call service methods and directly output the `AllActor` result without additional error handling
- this pushes error handling logic down to the service layer where business logic resides

## AllActor Pattern
- when services need to trigger infrastructure actions (tasks, messages), return `AllActor` type from `sebastian.protocols.models`
- `AllActor` contains:
    - `create_tasks: list[CreateTask]` - tasks to create in Google Tasks
    - `send_messages: list[SendMessage]` - messages to send via Telegram
- use helper functions to map domain models to `CreateTask`/`SendMessage` objects (e.g., `_map_to_create_task(pickup_data)`)
- Azure functions convert `AllActor` to `AllActorEventGrid` using `AllActorEventGrid.from_application(actor_result)`
- the `all_actor_handler` function then routes these to the appropriate infrastructure handlers

## Service-to-Service Dependencies
- when a service needs to depend on another service (e.g., MailToAllHandler depends on AllHandlerService):
    1. create a protocol in the dependent service's directory (e.g., `sebastian/usecases/AllHandler/protocol.py`)
    2. define the protocol interface with the required methods
    3. inject the service via the protocol in the dependent service's __init__
    4. add resolver in cloud/dependencies/usecases.py that injects both client and service dependencies
- this enables clean dependency injection and testability for complex service orchestrations

## Organizing Complex Services
- when a service grows complex with multiple responsibilities, consider splitting:
    1. keep core service logic in main service.py
    2. create subdirectories for specific responsibilities (e.g., `MailToAllHandler/`)
    3. subdirectories should have their own service.py and __init__.py
    4. use protocols to define interfaces between services
- example: AllHandlerService (core AI handling) + MailToAllHandler (email processing + AI handling)
