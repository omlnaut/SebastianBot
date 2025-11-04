# From investigation (notebook) to Azure Function

This guide outlines the general process for turning code explored in a notebook into a production Azure Function that integrates via Event Grid and an HTTP test route.
If steps are unclear, refer to the files in `infrastructure/google/task` for an example result of the below steps.

Deliverables (per service)
- Domain models and service wrapper (e.g., `XyzModels.py`, `XyzService.py`).
- Event payload schemas using pydantic (e.g., `XyzSchemas.py`).
- Azure helper for bindings and event construction (e.g., `XyzAzureHelper.py`).
- Azure Functions module with an HTTP emitter and an Event Grid trigger (e.g., `XyzFunction.py`).
- `function_app.py` updated to import the new functions so they are registered.

Process
1) Extract the service from the notebook
- Move pure data shapes into a models file (dataclasses for API responses).
   - check service implementation in notebook if it makes sense to create more models
- Move API-calling logic into a thin service wrapper with clear methods used by the function.
- if the notebook does not contain a ready service, but rather a collection of methods, collect them into a service class. extract the methods that are necessary for the task
- if it' a google service, check /workspaces/SebastianBot/infrastructure/google for shared helpers and example implementations

2) Define strict event schemas with pydantic
- Create pydantic models for Event Grid payloads. Example shape:
   - `title: str`
   - `notes: str | None`
   - `due: datetime | None`
- Let pydantic handle datetime parsing/validation and use `model_validate(...)` on incoming events.

3) Add an Azure helper for Event Grid
- Provide a `..._output_binding(arg_name: str = "...Output")` that returns `app.event_grid_output(...)` with your topic URI/key settings.
- Provide `create_..._output_event(event: <PydanticModel>, subject: str = "...") -> func.EventGridOutputEvent` that uses `event.model_dump()` for the `data` field.

4) Implement the Azure Functions
- for event grid triggered functions:
   - HTTP test route: construct a pydantic event model from simple request data and set it on the output binding to emit an Event Grid event.
   - Event Grid trigger: call `get_json()` on the event, parse strictly with the pydantic model (`model_validate`), then call the service using parsed fields.
   - On validation errors, log and return early.
- for timer based functions:
   - one timer triggered function, choose any cronstring. the user will change that later
   - HTTP test route: the logic in the timer function should be completly encapsulated in a private method. the test route invokes the same logic
   - see /workspaces/SebastianBot/usecases/manga_update/MangaUpdateFunction.py for example implementation

5) Wire functions for discovery
- Import the new functions in `function_app.py` so the `FunctionApp` registers them at startup.

6) Configuration and secrets
- Use existing secrets helpers for credentials (e.g., `shared.secrets.get_secret(...)`) and construct SDK credentials as needed.
- Reference Event Grid topic settings via environment configuration consumed in the helper (e.g., `..._EVENT_GRID_URI`, `..._EVENT_GRID_KEY`).

Edge cases to consider
- Missing required fields or invalid payloads (pydantic validation errors).
- Malformed or timezone-variant dates (let pydantic parse ISO8601; log/skip on failure).
- Upstream API failures (decide whether to catch/log or propagate based on desired retry behavior).
- Secret retrieval failures (Key Vault and identity configuration).