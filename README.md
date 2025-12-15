# SebastianBot

A personal hobby project focused on automating boring everyday tasks. Built as an exploration of Azure Functions, clean architecture, and GitHub Copilot agent-assisted development.

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
- **Clients**: Interact with external services (Gmail, Reddit, Telegram, Google Drive/Tasks)
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
| OnePunchMan | Checks for new One Punch Man chapters | Daily at 3:01 AM |
| SkeletonSoldier | Checks for new Skeleton Soldier chapters | Daily at 3:03 AM |
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
- Required credentials in Azure Key Vault (Reddit, Telegram, Google, etc.)

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
- Poetry for dependency management
- All Python dependencies pre-installed

### Testing

The project uses **pytest** for testing with a focus on the application layer (`sebastian/`).

**Run all tests:**
```bash
poetry run pytest
```

**Run with coverage:**
```bash
poetry run pytest --cov=sebastian --cov-report=html
```

**CI/CD:**
- Tests run automatically on pull requests and pushes to main via GitHub Actions
- Coverage reports are uploaded to Codecov for PR annotations
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
