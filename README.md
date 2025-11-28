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

- Python 3.x
- Azure Functions Core Tools
- Required credentials in Azure Key Vault (Reddit, Telegram, Google, etc.)

### Local Development

```bash
# Install dependencies
pip install -r requirements_local.txt

# Run functions locally
func start
```
