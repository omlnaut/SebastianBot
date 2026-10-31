# SebastianBot

A personal hobby project focused on automating boring everyday tasks. Built as an exploration of Azure Functions, pragmatic clean architecture, and GitHub Copilot agent-assisted development.

## Goals

- **Primary**: Automate repetitive tasks (package tracking, invoice management, manga updates, etc.)
- **Secondary**: Experiment with modern technologies (Azure hosting, GitHub Copilot agents)

## Architecture

The project follows clean architecture principles with a clear separation between infrastructure and application logic.

```
├── cloud/                    # Infrastructure layer (Azure)
│   ├── functions/            # Azure Functions (one per file)
│   ├── dependencies/         # Service and client resolvers
│   └── helper/               # Azure-specific utilities
│
├── sebastian/                # Application layer (core logic)
│   ├── clients/              # External service clients
│   ├── usecases/             # Business logic services
│   ├── infrastructure/       # Event-triggered infrastructure (Telegram, Google Tasks)
│   └── shared/               # Shared utilities
│
└── function_app.py           # Azure Functions entry point
```

### Layer Responsibilities

**Cloud Layer** (`cloud/`):
- Timer-triggered Azure Functions that run on schedules
- Dependency injection via resolvers in `dependencies/`
- Output bindings for Telegram notifications and Google Tasks

**Application Layer** (`sebastian/`):
- **Clients**: Interact with external services (Gmail, Telegram, Google Drive/Tasks)
- **Usecases**: Orchestrate clients with business logic (e.g., checking for DHL pickups, tracking manga updates)
- The application layer has no dependency on the cloud layer

### How Components Work Together

1. **Azure Functions** (cloud/functions/) are triggered by timers (see `TriggerTimes.py`)
2. Functions resolve **services** via `cloud/dependencies/services.py`
3. Services are injected with **clients** resolved from `cloud/dependencies/clients.py`
4. Services execute business logic and return results
5. Functions map results to **output bindings** (Telegram messages, Google Tasks)

## Current Automations

| Function | Description | Schedule |
|----------|-------------|----------|
| DeliveryReady | Checks Gmail for DHL pickup notifications | Hourly at :28 |
| ReturnTracker | Tracks return shipments | Hourly at :35 |
| MangaUpdate | Monitors manga update sources | Daily at 3:05 AM |
| WinSim | Archives WinSim invoices to Google Drive | Daily at 9:00 PM |
| Mietplan | Manages rental payment schedules | Daily at 9:01 PM |

## GitHub Copilot Agent Integration

The project extensively uses GitHub Copilot agents for assisted development. Instructions are organized under `.github/`:

- **`copilot-instructions.md`**: General coding guidelines, architecture principles, and style conventions
- **`instructions/`**: Task-specific instructions for:
  - Creating new Azure Functions
  - Creating new clients
  - Creating new services
- **`prompts/`**: Reusable prompts for common operations

These instruction files ensure consistent code generation that follows the project's clean architecture patterns.

## Development

### Prerequisites

- Docker
- VS Code with Dev Containers extension
- Required credentials in Azure Key Vault (Telegram, Google, MangaUpdate, etc.)

### Local Development

Development is done via **Dev Containers**, which automatically sets up the complete environment:

1. Open the project in VS Code
2. When prompted, click "Reopen in Container" (or run `Dev Containers: Reopen in Container` from command palette)
3. `Start Azure Blob Service` (bottom right in vscode)
4. In Azure extension, start debugging locally


The devcontainer includes:
- Python 3.12
- Azure Functions Core Tools
- Azure CLI
- GitHub CLI (`gh`)
- Poetry for dependency management
- All Python dependencies pre-installed

### GitHub CLI Authentication (safe setup)

If you want to manage repository settings (for example, branch protection and auto-merge rules) from inside the devcontainer, use `gh` with a token stored only in your local `.env` file.

1. Copy `.env.sample` to `.env`.
2. Create a fine-grained personal access token in GitHub.
3. Add it to `.env` as `GH_TOKEN=...`.
4. Rebuild or restart the devcontainer so the variable is injected.
5. Verify with `gh auth status`.

Security notes:
- `.env` is gitignored in this repository, so your token is not committed.
- Do not store tokens in tracked files like `README.md`, `pyproject.toml`, or workflow files.
- Prefer a fine-grained token scoped to this repository only, with minimum required permissions.

### Host CLI: `seamail`

`seamail` is a read-only Gmail recall CLI for agents: search with Gmail's own query syntax, read one mail in full, list labels, pull attachments. It runs as a plain short-lived host process — no container, no Azure login, no Key Vault — on WSL today and a Raspberry Pi later.

```bash
scripts/setup_seamail.sh   # idempotent: installs uv if missing, builds the venv, writes the PATH shim
export SEAMAIL_GOOGLE_CREDENTIALS="$(cat /path/to/credentials.json)"

seamail search 'from:installer subject:KfW after:2026/01/01'
seamail show <message-id> [--format text|html] [--max-chars 20000]
seamail labels
seamail attachments <message-id> --out ~/Downloads [--force]
```

- Every successful call prints one JSON object on stdout. Failures print JSON on stderr with a machine-readable `kind` (`auth`, `api`, `usage`, `io`); exit codes are `0` success, `1` runtime error, `2` usage error.
- API errors carry `status` and, when Gmail names one, `reason` alongside a single-sentence `message` (no Python repr or request URL): `{"kind": "api", "status": 404, "reason": "notFound", "message": "Requested entity was not found."}`. A `401` (expired/revoked token) or a permission `403` is reported as `kind: auth`; quota/rate-limit `403`s stay `api`.
- `attachments --out DIR` creates `DIR` (including parents) when missing; existing files are only replaced with `--force`.
- The CLI never writes to Gmail. Labels are resolved to names on every call; search returns metadata only and a `nextPageToken` instead of paginating for you.
- `SEAMAIL_GOOGLE_CREDENTIALS` holds the credentials JSON *content* (not a path); token refresh happens in-process and nothing is written back.
- Its dependencies are the direct ones listed in `cli-requirements.txt`; `pyproject.toml` stays the source of truth and `tests/unit_tests/test_cli_requirements.py` guards the two from drifting. The Azure deployment and `requirements.txt` are untouched.

### Testing

The project uses **pytest** for testing with a focus on the application layer (`sebastian/`).

**Test organization:**
- `tests/unit_tests/` - Unit tests (no external dependencies, run in CI)
- `tests/integration_tests/` - Integration tests (require credentials, run locally)

**Run all tests:**
```bash
poetry run pytest
```

**Run only unit tests:**
```bash
poetry run pytest tests/unit_tests
```

**Run with coverage:**
```bash
poetry run pytest tests/unit_tests --cov=sebastian --cov-report=html
```

**CI/CD:**
- Only unit tests run automatically in CI (fast, no credentials needed)
- Integration tests should be run locally before merging

- See [`.github/instructions/testing.instructions.md`](.github/instructions/testing.instructions.md) for detailed testing guidelines

### Dependency Management

This project uses **Poetry** for dependency management while maintaining compatibility with Azure Functions deployment via `requirements.txt`.

#### Adding Dependencies

**Production dependencies:**
```bash
poetry add <package-name>
```

**Development dependencies:**
```bash
poetry add --group dev <package-name>
```

**Test dependencies:**
```bash
poetry add --group test <package-name>
```

Both `pyproject.toml` and `poetry.lock` will be updated automatically.

#### Removing Dependencies

```bash
poetry remove <package-name>
```

#### Deployment to Azure

Azure Functions requires a `requirements.txt` file. A **pre-commit hook** automatically exports this file whenever `pyproject.toml` or `poetry.lock` changes, ensuring it stays in sync.

**CI Validation:**
The pull request pipeline automatically checks that `requirements.txt` is up-to-date. If the check fails, either:
- Commit your changes (the pre-commit hook will update it automatically), or
- Run the export command manually:
Committing your changes will only work if there are changes to `poetry.lock` or `pyproject.toml`
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

Only production dependencies are included in deployments—dev and test dependencies (pytest, ipykernel, etc.) are excluded.

For more details, see [`notes/dev_setup/dependencies.md`](notes/dev_setup/dependencies.md).
