# Feature Usecase: Complete Flow Reference

This document describes the complete end-to-end architecture for Feature Usecases — the preferred pattern for new functionality in SebastianBot. Use it as a reference when creating new usecases or refactoring existing ones.

The `delivery_ready` usecase is used throughout as the canonical example.

---

## End-to-End Flow

```
Azure Timer Trigger
    │
    ▼
cloud/functions/features/{name}_function.py
    │  perform_usecase_from_request(request, resolve_{name})
    ▼
cloud/dependencies/usecases.py :: resolve_{name}()
    │  instantiates Handler with concrete clients from cloud/dependencies/clients.py
    ▼
sebastian/usecases/features/{name}/handler.py :: Handler.handle(request)
    │  executes business logic, calls clients via protocol interfaces
    │  returns Sequence[BaseActorEvent] (e.g. CreateTask, SendMessage, ...)
    ▼
cloud/functions/side_effects/shared.py :: perform_usecase_from_request
    │  maps returned events to infrastructure EventGridModels via EVENT_MAP
    │  publishes each EventGridModel to its dedicated topic
    ▼
Side-effect EventGrid triggers (one per action type):
    ├── cloud/functions/side_effects/create_task/function.py
    ├── cloud/functions/side_effects/create_calendar_event/function.py
    ├── cloud/functions/side_effects/send_message/function.py
    ├── cloud/functions/side_effects/complete_task/function.py
    └── cloud/functions/side_effects/modify_mail_label/function.py
            │  each uses perform_usecase_from_eventgrid(create_request, resolve_handler, az_event)
            ▼
    sebastian/usecases/side_effects/{action}.py :: Handler.handle(request)
            │  executes the action (create task, send message, etc.)
            │  returns Sequence[BaseActorEvent] (e.g. a confirmation SendMessage after task creation)
            ▼
    Mapped and published to its respective EventGrid topic
```

---

## Directory Layout

```
sebastian/domain/
    {model}.py           # Shared data types used across usecases and clients

sebastian/usecases/features/{name}/
    __init__.py          # re-exports handler.py's __all__  (from .handler import *)
    handler.py           # Request dataclass, Handler class, __all__ with protocol re-exports
    protocols.py         # Protocol definitions for every external dependency
    parsing.py           # Complex parsing/transformation logic extracted from handler (optional)
    {name}.ipynb         # Notebook showcasing usage (optional)

cloud/functions/features/
    {name}_function.py   # Azure timer-trigger function for this usecase

cloud/dependencies/
    usecases.py          # resolve_{name}() — wires Handler to real clients
    clients.py           # resolve_{client}() — instantiates real client objects
```

---

## Application Layer (`sebastian/`)

### 1. Domain Models (`sebastian/domain/`)

Domain models represent shared data structures that may be used across multiple usecases or clients.

- Place shared data types (e.g. `FullMailResponse`, `Task`, `TaskLists`) in `sebastian/domain/`.
- Domain models are **pure**: no `ConfigDict(extra="allow")`, no parsing logic. They are mapped *to* from API response models, not parsed directly from external JSON.
- Use plain `@dataclass` or `pydantic.BaseModel` without `extra` constraints.
- **API response models** (direct JSON parsing from external services) live in the client's `_models.py` and use `ConfigDict(extra="allow")` to tolerate unexpected fields. Mapping from API response → domain model is done in the service wrapper (`service_wrapper.py`) via module-level `_to_*` helper functions, not inside the domain model itself.

```python
# sebastian/domain/task.py
from enum import Enum, auto
from pydantic import BaseModel, Field

class TaskLists(Enum):
    Default = auto()
    Mangas = auto()
    Bibo = auto()

class Task(BaseModel):
    id: str = Field(..., min_length=1)
    tasklist: TaskLists
    title: str = Field(..., min_length=1)
    due: datetime | None = None
    notes: str | None = None
```

When adding a new tasklist category, add a new member to `TaskLists`.

---

### 2. Protocols (`protocols.py`)

Protocols define the interface the Handler expects from each external dependency, enabling dependency injection and testability.

- Define **one Protocol per external dependency**.
- Protocols are **co-located with the usecase** (not in `sebastian/protocols/`).
- Export every protocol class via `__all__` so the resolver can reference them as `{module}.ProtocolName`.

```python
# sebastian/usecases/features/delivery_ready/protocols.py
from typing import Protocol, TypeVar
from pydantic import BaseModel
from sebastian.domain.gmail import FullMailResponse

__all__ = ["GmailClient", "GeminiClient"]

T = TypeVar("T", bound=BaseModel)

class GeminiClient(Protocol):
    def get_response(self, prompt: str, response_schema: type[T]) -> T: ...

class GmailClient(Protocol):
    def fetch_mails(self, query: str) -> list[FullMailResponse]: ...
```

---

### 3. `handler.py` — Request, Handler, and `__all__`

`handler.py` is the core of every feature usecase. It contains exactly three things:

1. **`Request`** — a `@dataclass` carrying all input parameters.
2. **`Handler(UseCaseHandler[Request])`** — implements `handle(request) -> Sequence[BaseActorEvent]`.
3. **`__all__`** — re-exports `Request`, `Handler`, and every protocol name.

```python
# sebastian/usecases/features/delivery_ready/handler.py
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging

from typing import Sequence

from sebastian.domain.task import TaskLists
from sebastian.protocols.models import BaseActorEvent, CreateTask, SendMessage
from sebastian.shared.gmail.query_builder import GmailQueryBuilder
from sebastian.usecases.usecase_handler import UseCaseHandler

from .parsing import PickupData, parse_dhl_pickup_email_html
from .protocols import GmailClient, GeminiClient

__all__ = ["Request", "Handler", "GmailClient", "GeminiClient"]


@dataclass
class Request:
    hours_back: timedelta = timedelta(hours=1)


class Handler(UseCaseHandler[Request]):
    def __init__(self, gmail_client: GmailClient, gemini_client: GeminiClient):
        self._gmail_client = gmail_client
        self._gemini_client = gemini_client

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        time_threshold = datetime.now(timezone.utc) - request.hours_back
        query = (
            GmailQueryBuilder()
            .from_email("order-update@amazon.de")
            .subject("Ihr Paket kann bei DHL", exact=True)
            .after_date(time_threshold)
            .build()
        )
        mails = self._gmail_client.fetch_mails(query)
        logging.info(f"Fetched {len(mails)} emails matching DHL pickup criteria")

        pickups: list[CreateTask] = []
        errors: list[SendMessage] = []

        for mail in mails:
            try:
                pickup_data = parse_dhl_pickup_email_html(mail.content, self._gemini_client)
                pickups.append(_map_to_create_task(pickup_data))
            except Exception as e:
                errors.append(SendMessage(message=f"Error parsing email: {str(e)}"))

        return [*pickups, *errors]


def _map_to_create_task(pickup: PickupData) -> CreateTask:
    notes = f"{pickup.item}\nAbholort: {pickup.pickup_location}"
    if pickup.due_date:
        notes += f"\nBis: {pickup.due_date.strftime('%d.%m.%Y')}"
    if pickup.tracking_number:
        notes += f"\nTracking: {pickup.tracking_number}"
    return CreateTask(title=f"Paket abholen: {pickup.item}", notes=notes, tasklist=TaskLists.Default)
```

**Handler conventions:**
- `handle()` is the single public entry point; it orchestrates calls to private methods.
- **Do not wrap the entire `handle()` body in `try/except`.** Both `perform_usecase_from_request` and `perform_usecase_from_eventgrid` already catch unhandled exceptions and forward them as a Telegram error message — adding a top-level `try/except` would suppress that mechanism.
- Per-item `try/except` is acceptable when processing a list and you want to continue with remaining items despite one failure. In that case, convert the exception to a `SendMessage` and include it in the returned list so the error is surfaced via Telegram.

---

### 4. `Sequence[BaseActorEvent]` — Return Type

Every `Handler.handle()` returns a list of objects deriving from `BaseActorEvent` (found in `sebastian.protocols.models`). These define actions to be executed by the infrastructure layer. Supported event types include:

| Actor Event | Effect |
|---|---|
| `CreateTask` | Creates a task in Google Tasks |
| `CreateCalendarEvent` | Creates a calendar event in Google Calendar |
| `CompleteTask` | Marks an existing task as complete |
| `SendMessage` | Sends a Telegram message |
| `ModifyMailLabel` | Adds or removes Gmail labels |

Unhandled exceptions propagate to `perform_usecase_from_request` / `perform_usecase_from_eventgrid`, which catch them and forward an error `SendMessage` automatically. Only convert exceptions to `SendMessage` yourself when processing a list and you want to continue despite individual item failures.

---

### 5. `parsing.py` — Extracted Parsing Logic (optional)

When a usecase involves complex parsing or transformation logic (e.g. stripping HTML and feeding the result to an AI model), that logic is extracted into a separate `parsing.py` file to keep `handler.py` readable.

`parsing.py` may define data models specific to its parsing logic (e.g. a schema used as the AI response type). These are not domain models — domain models always live in `sebastian/domain/`.

```python
# sebastian/usecases/features/delivery_ready/parsing.py
from datetime import date
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from .protocols import GeminiClient

class PickupData(BaseModel):
    tracking_number: str = Field(description="The DHL tracking number of the package.")
    pickup_location: str = Field(
        description="When location is Packstation, only include 'Packstation <Number>' as location."
    )
    due_date: date
    item: str = Field(description="Description of the item to be picked up")

def parse_dhl_pickup_email_html(html: str, gemini_client: GeminiClient) -> PickupData:
    soup = BeautifulSoup(html, "html.parser")
    text_content = soup.get_text()
    prompt = f"""Given the following email text, extract all relevant information:
--- email text start ---
{text_content}
--- email text end ---
Current year is {date.today().year}
"""
    return gemini_client.get_response(prompt, response_schema=PickupData)
```

---

### 6. `__init__.py`

```python
# sebastian/usecases/features/{name}/__init__.py
from .handler import *
```

This single line re-exports everything declared in `__all__` inside `handler.py`, making `delivery_ready.Request`, `delivery_ready.Handler`, `delivery_ready.GmailClient`, etc. available via the module alias.

---

## Cloud Layer (`cloud/`)

### 7. Secrets (`cloud/helper/secrets.py`)

Secrets are stored in **Azure Key Vault** and accessed via `get_secret()`.

```python
from cloud.helper import SecretKeys, get_secret

# Retrieve and parse a secret into its associated pydantic model:
credentials = get_secret(SecretKeys.GeminiApiKey)
```

`SecretKeys` contains `TypedSecretKey` constants mapping readable names to Key Vault secret names and their target model types:

```python
class SecretKeys:
    TelegramSebastianToken: TypedSecretKey[_TelegramConfig] = TypedSecretKey("SebastianTelegramToken", _TelegramConfig)
    GoogleCredentials: TypedSecretKey[_GoogleSecret] = TypedSecretKey("GoogleCredentials", _GoogleSecret)
    MangaUpdateCredentials: TypedSecretKey[_MangaUpdateSecret] = TypedSecretKey("MangaUpdateCredentials", _MangaUpdateSecret)
    MietplanCredentials: TypedSecretKey[_MietplanCredentials] = TypedSecretKey("MietplanCredentials", _MietplanCredentials)
    GeminiApiKey: TypedSecretKey[_GeminiApiKey] = TypedSecretKey("GeminiApiKey", _GeminiApiKey)
    BiboCredentials: TypedSecretKey[_BiboCredentials] = TypedSecretKey("BiboCredentials", _BiboCredentials)
```

**To add a new secret:**
1. Store the secret value in the Azure Key Vault (e.g. as JSON matching the credential model).
2. Create a credentials model (pydantic `BaseModel`) in the client's directory.
3. Import the model in `cloud/helper/secrets.py` and add a new `TypedSecretKey` to `SecretKeys`.
4. Use `get_secret(SecretKeys.YourNewKey)` in the client resolver.

Google API credentials (Gmail, Tasks, Drive, Calendar) use OAuth2 credentials stored under `SecretKeys.GoogleCredentials` and are loaded via `cloud/functions/infrastructure/google/helper.py :: load_google_credentials()`. If a new Google API scope is required, update `investigations/google_token/create_credentials.py` and re-run it to generate a new token.

---

### 8. Client Resolvers (`cloud/dependencies/clients.py`)

Client resolvers are cached factory functions that instantiate real client objects from credentials.

```python
# cloud/dependencies/clients.py
@lru_cache()
def resolve_gemini_client() -> GeminiClient:
    credentials = get_secret(SecretKeys.GeminiApiKey)
    return GeminiClient(credentials)

@lru_cache()
def resolve_gmail_client() -> GmailClient:
    credentials = load_google_credentials()
    return GmailClient(credentials)
```

- `@lru_cache()` ensures the client is only instantiated once per function app instance.
- Add a new `resolve_{client}()` function here whenever a new client is created.

---

### 9. Usecase Resolver (`cloud/dependencies/usecases.py`)

The usecase resolver wires the `Handler` to real clients and is the entry point for the cloud layer.

```python
# cloud/dependencies/usecases.py
from sebastian.usecases.features import delivery_ready
from sebastian.usecases.usecase_handler import UseCaseHandler

def resolve_delivery_ready(
    gmail_client: delivery_ready.GmailClient | None = None,
    gemini_client: delivery_ready.GeminiClient | None = None,
) -> UseCaseHandler[delivery_ready.Request]:
    return delivery_ready.Handler(
        gmail_client=gmail_client or resolve_gmail_client(),
        gemini_client=gemini_client or resolve_gemini_client(),
    )
```

Key rules:
- Return type is always `UseCaseHandler[{name}.Request]` (not the concrete `Handler`).
- Protocol types are referenced via the module alias (`delivery_ready.GmailClient`) — this works because they are re-exported in `handler.py`'s `__all__`.
- All client parameters default to `None` so that tests can inject mock clients.

---

### 10. Trigger Times (`cloud/functions/TriggerTimes.py`)

All cron schedules are centralised here. Add one entry per usecase.

```python
class TriggerTimes:
    DeliveryReady: str = "28 * * * *"    # Every hour at minute 28
    MangaUpdate:   str = "5 3 * * *"     # Every day at 03:05
    BiboLendingSync: str = "0 8 * * *"   # Every day at 08:00
```

Cron format: `"min hour day month dayofweek"` (Azure Functions / NCrontab syntax).

---

### 11. Azure Function (`cloud/functions/features/{name}_function.py`)

The function is a thin wrapper: construct `Request` → call `perform_usecase_from_request`.

```python
# cloud/functions/features/delivery_ready_function.py
from datetime import timedelta
import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_delivery_ready
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import delivery_ready
from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.DeliveryReady,
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_delivery_ready(mytimer: TimerRequest) -> None:
    logging.info("DeliveryReady timer function processed a request.")
    perform_usecase_from_request(
        delivery_ready.Request(hours_back=timedelta(hours=1)),
        resolve_delivery_ready,
    )
```

`perform_usecase_from_request` (from `cloud/functions/side_effects/shared.py`):
1. Calls `resolve_delivery_ready()` to get a `Handler`.
2. Calls `handler.handle(request)` to get a `Sequence[BaseActorEvent]`.
3. Maps returned events to EventGrid models using `EVENT_MAP` and publishes them.
4. If an unhandled exception occurs, sends a `SendMessage` with the error text to Telegram.

---

### 12. `function_app.py` Registration

Every Azure Function must be imported in `function_app.py` to be registered with the Azure Functions runtime.

```python
# function_app.py
from cloud.functions.features.delivery_ready_function import check_delivery_ready
```

Add the import after implementing the function file. Without it the function will not be discovered.

---

### 13. EventGrid Infrastructure and Side Effects

In `perform_usecase_from_request`, the `Sequence[BaseActorEvent]` is mapped to dedicated EventGrid models using the `EVENT_MAP` in `cloud/functions/side_effects/shared.py`. They are then published directly to dedicated EventGrid topics:
- `CreateTask` → `CreateTaskEventGrid` topic
- `CreateCalendarEvent` → `CreateCalendarEventEventGrid` topic
- `CompleteTask` → `CompleteTaskEventGrid` topic
- `SendMessage` → `SendTelegramMessageEventGrid` topic
- `ModifyMailLabel` → `ModifyMailLabelEventGrid` topic

**Side-effect functions** each subscribe to their topic and execute the action using their own usecase handler.

#### Side-effect function structure

Side-effect functions differ from feature usecase functions in two key ways:
- They are **EventGrid-triggered** (not timer-triggered).
- They use **`perform_usecase_from_eventgrid`** instead of `perform_usecase_from_request`.

```python
# cloud/functions/side_effects/create_task/function.py
@app.event_grid_trigger(arg_name="azeventgrid")
def create_task(azeventgrid: func.EventGridEvent):
    def create_request(event: CreateTaskEventGrid) -> usecases.create_task.Request:
        return usecases.create_task.Request(
            tasklist=event.tasklist,
            title=event.title,
            notes=event.notes or "",
            due_date=event.due,
        )

    perform_usecase_from_eventgrid(
        create_request,
        usecases.resolve_create_task,
        azeventgrid,
    )
```

`perform_usecase_from_eventgrid(create_request, resolve_handler, az_event)`:
1. Reads the event model type from `create_request`'s type hint.
2. Parses the raw Azure EventGrid event into that model (e.g. `CreateTaskEventGrid`).
3. Calls `create_request(event)` to build the usecase `Request`.
4. Calls `resolve_handler()` to get the `Handler`.
5. Calls `handler.handle(request)` → returns `Sequence[BaseActorEvent]`.
6. Maps returned events via `EVENT_MAP` and publishes them to their respective EventGrid topics (so side effects can themselves produce further actions, e.g. `create_task` returns a confirmation `SendMessage`).
7. On any exception: logs the error and publishes an error `SendTelegramMessageEventGrid`.

#### Side-effect usecases (`sebastian/usecases/side_effects/`)

Each side-effect function has a corresponding usecase in `sebastian/usecases/side_effects/`. These follow the same `Request` / `Handler` / Protocol pattern as feature usecases, but live in a separate directory:

```
sebastian/usecases/side_effects/
    create_task.py           # Request, Handler, TaskClient protocol
    create_calendar_event.py # Request, Handler, CalendarEventClient protocol
    complete_task.py         # Request, Handler, TaskClient protocol
    send_telegram_message.py # Request, Handler, TelegramClient protocol
    modify_mail_labels.py    # Request, Handler, GmailClient protocol
```

Their handlers also return `Sequence[BaseActorEvent]` — for example, the `create_task` handler returns a `SendMessage` confirmation after creating the task.

#### EventGrid Environment Variables

Each EventGrid topic requires one environment variable named after the `EventGridModel` class (e.g. `CreateTaskEventGrid`). Its value is a JSON object with `uri` and `key`:

| Variable | Value format |
|---|---|
| `{EventGridModelClassName}` | `{"uri": "<topic-endpoint>", "key": "<access-key>"}` |

In `local.settings.json` the JSON value must be stored as a string with escaped quotes (e.g. `"{\"uri\": \"...\", \"key\": \"...\"}"`).

These are loaded automatically by `send_eventgrid_events()` via `event_type.env_name()` in `cloud/functions/side_effects/shared.py`.

**Automated setup:** Use the notebook `cloud/helper/eventgrid_wiring/eventgrid_wiring.ipynb` to automate the full setup: creating the EventGrid topic, creating a subscription to the Azure Function, retrieving the endpoint and key, and writing the env var to both the Function App application settings and `local.settings.json`.

---

## Complete Worked Example: `delivery_ready`

### What it does
Checks Gmail every hour for DHL pickup-ready notifications from Amazon, extracts structured pickup data using Gemini AI, and creates a Google Task for each parcel.

### Files created

| File | Purpose |
|---|---|
| `sebastian/usecases/features/delivery_ready/__init__.py` | `from .handler import *` |
| `sebastian/usecases/features/delivery_ready/protocols.py` | `GmailClient`, `GeminiClient` protocols |
| `sebastian/usecases/features/delivery_ready/parsing.py` | `PickupData` model + `parse_dhl_pickup_email_html()` |
| `sebastian/usecases/features/delivery_ready/handler.py` | `Request`, `Handler`, `__all__` |
| `cloud/functions/features/delivery_ready_function.py` | Timer-triggered Azure Function |
| `cloud/functions/TriggerTimes.py` | `DeliveryReady = "28 * * * *"` added |
| `cloud/dependencies/usecases.py` | `resolve_delivery_ready()` added |
| `function_app.py` | `from cloud.functions.features.delivery_ready_function import check_delivery_ready` added |

### Data flow
```
Timer fires every hour
    → check_delivery_ready(mytimer)
    → perform_usecase_from_request(
          Request(hours_back=timedelta(hours=1)),
          resolve_delivery_ready
      )
    → resolve_delivery_ready()
          → GmailClient(google_credentials)
          → GeminiClient(gemini_api_key)
          → Handler(gmail_client, gemini_client)
    → Handler.handle(request)
          → build Gmail query: from:order-update@amazon.de subject:"Ihr Paket kann bei DHL" after:<timestamp>
          → gmail_client.fetch_mails(query)  →  [FullMailResponse, ...]
          → for each mail:
                parse_dhl_pickup_email_html(mail.content, gemini_client)
                    → BeautifulSoup strips HTML → plain text
                    → gemini_client.get_response(prompt, PickupData)
                    → returns PickupData(tracking_number, pickup_location, due_date, item)
                → _map_to_create_task(pickup_data)
                    → CreateTask(title="Paket abholen: ...", notes="...", tasklist=TaskLists.Default)
          → returns [CreateTask(...)]
    → maps CreateTask to CreateTaskEventGrid via EVENT_MAP
    → publishes CreateTaskEventGrid directly to its EventGrid topic
    → create_task function receives CreateTaskEventGrid
    → GoogleTaskClient.create_task(...)
```

---

## Full Checklist for Creating a New Feature Usecase

### Application layer

- [ ] Create `sebastian/usecases/features/{name}/` directory
- [ ] Create `sebastian/usecases/features/{name}/__init__.py` with `from .handler import *`
- [ ] Create `sebastian/usecases/features/{name}/protocols.py`:
  - One `Protocol` per external dependency
  - Export all via `__all__`
- [ ] Create `sebastian/usecases/features/{name}/handler.py`:
  - `@dataclass class Request`
  - `class Handler(UseCaseHandler[Request])` with `handle(request) -> Sequence[BaseActorEvent]`
  - `__all__` re-exporting `Request`, `Handler`, and all protocol names
- [ ] If parsing logic is non-trivial: create `parsing.py` with parsing functions
- [ ] If using domain types (e.g. a new task list): add to `sebastian/domain/` as needed
- [ ] Optional: create `{name}.ipynb` notebook showcasing usage

### Secrets (if new credentials are required)

- [ ] Store the new secret in Azure Key Vault as JSON
- [ ] Add a new member to `SecretKeys` in `cloud/helper/secrets.py`
- [ ] Create a credentials pydantic model in the client's directory
- [ ] If using Google APIs with a new scope: update `investigations/google_token/create_credentials.py` and regenerate the token

### Client (if a new client is required)

- [ ] Create `sebastian/clients/{name}/client.py` implementing the client
- [ ] Add `resolve_{name}_client()` to `cloud/dependencies/clients.py` using `@lru_cache()`

### Cloud layer

- [ ] Add trigger time to `cloud/functions/TriggerTimes.py` in cron format
- [ ] Create `cloud/functions/features/{name}_function.py`:
  - `@app.timer_trigger` with `schedule=TriggerTimes.{Name}`, `run_on_startup=False`, `use_monitor=False`
  - Function named `check_{name}(mytimer: TimerRequest) -> None`
  - Calls `perform_usecase_from_request({name}.Request(...), resolve_{name})`
- [ ] Add `resolve_{name}()` to `cloud/dependencies/usecases.py`:
  - Return type `UseCaseHandler[{name}.Request]`
  - All client params defaulting to `None` for test injection
- [ ] Import the function in `function_app.py`

### EventGrid (if new action types are needed)

- [ ] Add new domain event derived from `BaseActorEvent` in `sebastian/protocols/models.py`
- [ ] Add new `EventGridModel` subclass under `cloud/functions/side_effects/{action}/models.py`
- [ ] Add the mapping from domain model to `EventGridModel` in `EVENT_MAP` inside `cloud/functions/side_effects/shared.py`
- [ ] Create the side-effect function in `cloud/functions/side_effects/{action}/function.py`
- [ ] Run `cloud/helper/eventgrid_wiring/eventgrid_wiring.ipynb` to create the topic, subscription, and set `{EventGridModelClassName}` env var in the Function App and `local.settings.json`
- [ ] Import the new side-effect function in `function_app.py`
