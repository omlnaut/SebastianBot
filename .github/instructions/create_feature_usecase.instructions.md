# Feature Usecase Structure

"Feature" usecases represent the new preferred structure for usecases. They differ from the older service-based usecases (e.g. `ReturnTracker`, `MangaUpdate`) in several key ways described below.

---

## Directory Layout

```
sebastian/usecases/features/{name}/
    __init__.py          # empty
    handler.py           # Request model, Handler class, protocol re-exports via __all__
    protocols.py         # protocols for all external dependencies (co-located with usecase)
    parsing.py           # domain parsing / transformation logic (if needed)
    {name}.ipynb         # notebook showcasing usage (if applicable)

cloud/functions/features/
    {name}_function.py   # Azure Function for this usecase
```

---

## Application Layer (`sebastian/usecases/features/{name}/`)

### `protocols.py`
- Define one `Protocol` per external dependency the handler needs
- Protocols are **specific to this usecase** (not shared from `sebastian/protocols/`)
- Export each protocol class via `__all__`

```python
from typing import Protocol
from sebastian.domain.gmail import FullMailResponse

__all__ = ["GmailClient"]

class GmailClient(Protocol):
    def fetch_mails(self, query: str) -> list[FullMailResponse]: ...
```

### `handler.py`
Contains three things, all in one file:

1. **`Request`** — a `@dataclass` for the usecase input. Use `timedelta` for time span parameters.
2. **`Handler`** — extends `UseCaseHandler[Request]`. Implements a single `handle(self, request: Request) -> AllActor` method.
3. **`__all__`** — re-exports `Request`, `Handler`, and all protocol names so the resolver can reference them as `{module}.ProtocolName`.

```python
from dataclasses import dataclass
from datetime import timedelta

from sebastian.protocols.models import AllActor
from sebastian.usecases.usecase_handler import UseCaseHandler
from .protocols import SomeClient

__all__ = ["Request", "Handler", "SomeClient"]

@dataclass
class Request:
    time_back: timedelta = timedelta(hours=1)

class Handler(UseCaseHandler[Request]):
    def __init__(self, some_client: SomeClient):
        self._some_client = some_client

    def handle(self, request: Request) -> AllActor:
        ...
```

**Handler conventions:**
- Public `handle()` orchestrates calls to private methods
- Private methods (`_do_something`) do not call other private methods
- Error handling lives here: `try/except` per item, errors go into `AllActor.send_messages`
- Module-level private helpers (e.g. `_map_to_create_task`) are fine for mapping logic

### `parsing.py`
- Contains `@dataclass` domain models (plain data containers, no pydantic needed unless parsing external JSON)
- Contains parsing functions used by the handler
- Mark with `# pyright: basic` if third-party types are involved

---

## Cloud Layer (`cloud/functions/features/{name}_function.py`)

```python
from datetime import timedelta
import logging

from azure.functions import TimerRequest

from cloud.dependencies.usecases import resolve_{name}
from cloud.functions.side_effects.shared import perform_usecase_from_request
from function_app import app
from sebastian.usecases.features import {name}
from ..TriggerTimes import TriggerTimes


@app.timer_trigger(
    schedule=TriggerTimes.{Name},
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False,
)
def check_{name}(mytimer: TimerRequest) -> None:
    logging.info("{Name} timer function processed a request.")

    perform_usecase_from_request(
        {name}.Request(time_back=timedelta(hours=1)), resolve_{name}
    )
```

- Uses `perform_usecase_from_request(request, resolver)` — **not** the old pattern of calling the service method and manually sending EventGrid events
- The `Request` is constructed directly with its parameters
- Function lives in `cloud/functions/features/` (not `cloud/functions/`)

---

## Resolver (`cloud/dependencies/usecases.py`)

```python
from sebastian.usecases.features import {name}
from sebastian.usecases.usecase_handler import UseCaseHandler

def resolve_{name}(
    some_client: {name}.SomeClient | None = None,
) -> UseCaseHandler[{name}.Request]:
    return {name}.Handler(
        some_client=some_client or resolve_some_client(),
    )
```

- Return type is always `UseCaseHandler[{name}.Request]`, not the concrete `Handler`
- Protocol types are referenced via the module alias (`{name}.SomeClient`) — possible because they are re-exported in `__all__` of `handler.py`
- Optional client args allow test injection

---

## Comparison: Old vs. New Pattern

| Aspect | Old (`*Service`) | New (`features/`) |
|---|---|---|
| Class name | `{Name}Service` | `Handler` |
| Base class | None | `UseCaseHandler[Request]` |
| Entry method | Named (e.g. `get_recent_returns()`) | Single `handle(request)` |
| Input | Method parameters | `Request` dataclass |
| Protocols | In `sebastian/protocols/` (shared) | Co-located in `protocols.py` |
| Public API | `__init__.py` re-exports | `__all__` in `handler.py` |
| Cloud function | Manually calls service + sends events | `perform_usecase_from_request(...)` |
| Function location | `cloud/functions/` | `cloud/functions/features/` |

---

## Checklist for Creating a New Feature Usecase

1. [ ] Create `sebastian/usecases/features/{name}/` with empty `__init__.py`
2. [ ] Write `protocols.py` with a `Protocol` per external dependency; export via `__all__`
3. [ ] Write `handler.py` with `Request` dataclass, `Handler(UseCaseHandler[Request])`, and `__all__`
4. [ ] Add `parsing.py` if parsing logic is non-trivial
5. [ ] Add trigger time to `cloud/functions/TriggerTimes.py`
6. [ ] Write `cloud/functions/features/{name}_function.py` using `perform_usecase_from_request`
7. [ ] Add `resolve_{name}` to `cloud/dependencies/usecases.py` returning `UseCaseHandler[{name}.Request]`
