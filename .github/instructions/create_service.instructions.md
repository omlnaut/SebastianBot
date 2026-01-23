# When creating a new service (usecase), follow these instructions:
- put into usecases dir, each usecase in its own folder
- create a service.py file containing the service class
- services orchestrate clients and business logic
- services should:
    - accept clients via dependency injection in __init__, using protocol types from sebastian/protocols/
    - return Result[T] for operations that can fail
    - return plain types (list, objects) for operations that always succeed
    - extract domain models in a models.py (pydantic models if parsing is involved, dataclasses otherwise)
    - extract parsing/transformation/logic into separate files if complex
- services must not depend on cloud/infrastructure layer (Azure functions, etc.)
- follow naming convention: {UseCase}Service (e.g., DeliveryReadyService, MangaUpdateService)
- when creating from a notebook: add a section that showcases the usage of the service
- add service resolver in cloud/dependencies/usecases.py (injecting required clients)
- when creating a new service, also create a notebook showcasing the usage. if a notebook alreaddy exists for the service, add to that one instead
- make configuration values, such as time-based thresholds, parameters to the public methods
    - use `timedelta` for any time span arguments (e.g. instead of `hours_back: int`, prefer `time_back: timedelta`)

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
