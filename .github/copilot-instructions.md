# SebastianBot - Copilot Instructions

## Repository Overview

**What it does**: SebastianBot is an Azure Functions-based Python bot that monitors manga updates, creates Google Tasks, and sends Telegram notifications. It runs scheduled checks for manga releases and integrates with external APIs.

**Project Type**: Azure Functions v4 Python application (~728 lines of code)
- **Language**: Python 3.12
- **Runtime**: Azure Functions Runtime v4
- **Frameworks**: azure-functions, python-telegram-bot, google-api-python-client, pydantic
- **Cloud Services**: Azure Functions, Azure Key Vault, Azure Event Grid, Google Tasks API

## Building and Testing

### Initial Setup

**ALWAYS run these steps in order before any other commands:**

1. **Install dependencies** (required before any testing or validation):
   ```bash
   pip install -r requirements_local.txt
   ```
   - This installs both production (`requirements.txt`) and development dependencies (`requirements_local.txt`)
   - Takes approximately 30-60 seconds
   - Includes: pytest, pytest-cov, ipykernel, azure-functions, python-telegram-bot, azure-identity, azure-keyvault-secrets, pydantic, google-auth-oauthlib, google-api-python-client

2. **Validate installation**:
   ```bash
   python3 -c "import function_app; print('Import successful')"
   ```
   - Must succeed without errors before proceeding

### Running Tests

**Test command** (run after any code change):
```bash
python3 -m pytest tests/ -v
```
- Expected: 5 tests in `tests/test_dates.py` should pass
- Takes less than 1 second
- Tests validate date utility functions in `shared/dates.py`

**Test with coverage**:
```bash
python3 -m pytest tests/ --cov=. --cov-report=term-missing
```
- Current coverage baseline: ~69% overall (shared/dates.py has 100% coverage)
- Takes less than 1 second

### Validation Steps

**Syntax validation** (quick check):
```bash
python3 -m py_compile function_app.py
```

**Import validation** (ensures no import errors):
```bash
python3 -c "import function_app"
```

### Linting and Formatting

**No linter or formatter is currently configured**. The project does not use black, flake8, pylint, or similar tools. Code style should match existing code conventions:
- Use type hints where present
- Follow PEP 8 conventions
- Match indentation and naming patterns in existing files

### Running Locally

**Azure Functions Core Tools** (`func`) is NOT installed in the standard environment. Local execution requires:
1. Dev container setup (see `.devcontainer/`)
2. Azurite for local storage emulation
3. Azure Functions Core Tools (installed via dev container feature)
4. Local settings file (not in repo, see `local.settings.json` in `.funcignore`)

**To start the function app in dev container**:
```bash
func host start
```
- Starts on default port (usually 7071)
- Requires Azurite to be running
- Requires local.settings.json with connection strings

## Project Structure

### Root Directory Layout

```
.
├── function_app.py          # Main Azure Functions app definition and function imports
├── host.json                # Azure Functions host configuration
├── requirements.txt         # Production dependencies
├── requirements_local.txt   # Development dependencies (pytest, ipykernel, etc.)
├── .funcignore             # Files to exclude from deployment
├── .gitignore              # Standard Python + Azure Functions gitignore
├── shared/                  # Common utilities used across functions
├── infrastructure/          # External service integrations (Google, Telegram)
├── usecases/               # Business logic (manga updates)
├── tests/                  # Test files
├── .devcontainer/          # Dev container configuration
├── .vscode/                # VS Code settings and tasks
├── google_token/           # Google OAuth token storage (gitignored)
├── investigations/         # Jupyter notebooks for exploration
└── notes/                  # Development documentation
```

### Key Source Files

**Main Application** (`function_app.py`):
- Entry point that creates the `FunctionApp` instance
- Imports and registers all Azure Functions from subdirectories
- Currently registered functions: `create_task`, `test_create_task`, `send_telegram_message`, `test_send_telegram_message`, `check_manga_update`

**Shared Utilities** (`shared/`):
- `secrets.py`: Azure Key Vault integration using DefaultAzureCredential
  - `SecretKeys` enum: TelegramSebastianToken, GoogleCredentials, MangaUpdateCredentials
  - `get_secret()`: Retrieves secrets and parses into Pydantic models
  - Key Vault URL: `https://omlnaut-sebastian.vault.azure.net/`
- `dates.py`: Date utilities with Berlin timezone
  - `get_end_of_day()`: Returns 23:59:59 in Europe/Berlin timezone
  - `is_at_most_one_day_old()`: Checks if date is within last day
- `azure_helper.py`: Event Grid payload parsing with Pydantic

**Infrastructure** (`infrastructure/`):
- `google/`: Google Tasks API integration
  - `GoogleAzureHelper.py`: Loads Google OAuth credentials from Key Vault
  - `task/TaskService.py`: Google Tasks API service (create tasks, list task lists)
  - `task/TaskFunction.py`: Azure Functions for task creation (HTTP + Event Grid)
  - `task/TaskModels.py`: Pydantic models and `TaskListIds` enum
  - `task/TaskSchemas.py`: Event schemas for task creation
- `telegram/`: Telegram bot integration
  - `TelegramService.py`: Sends messages via python-telegram-bot
  - `TelegramFunction.py`: Azure Functions for sending messages (HTTP + Event Grid)
  - `TelegramSecret.py`: Pydantic models for Telegram configuration
  - `AzureHelper.py`: Event Grid output binding helpers

**Use Cases** (`usecases/`):
- `manga_update/`: Manga release monitoring
  - `MangaUpdateFunction.py`: Timer-triggered function (daily at 3:07 AM)
  - `MangaUpdateService.py`: Calls MangaUpdates.com API
  - `MangaModels.py`: Data models for manga and chapters

### Configuration Files

**Azure Functions Configuration**:
- `host.json`: Runtime version 2.0, extension bundle v4
- `.vscode/settings.json`: Python runtime v4, language model 2, scmDoBuildDuringDeployment enabled
- `.vscode/launch.json`: Debugger attaches to port 9091
- `.vscode/tasks.json`: "func: host start" task

**Dev Container** (`.devcontainer/`):
- `Dockerfile`: Python 3.12-bullseye base image
- `devcontainer.json`: Installs azure-cli and azure-functions-core-tools features
- VS Code extensions: black-formatter, python, azure-pack, jupyter, azurite

### Important Dependencies

**Not obvious from structure**:
- All functions require Azure Key Vault access via Managed Identity (configured in Azure portal)
- Google functions need OAuth credentials stored in Key Vault as "GoogleCredentials"
- Telegram functions need bot token stored in Key Vault as "SebastianTelegramToken"
- Manga updates need MangaUpdates API credentials as "MangaUpdateCredentials"
- Event Grid topics are used for inter-function communication (tasks trigger Telegram notifications)

### Testing Infrastructure

- Test framework: pytest (with pytest-cov plugin)
- Test location: `tests/` directory
- Current tests: Only `test_dates.py` with 5 tests
- No integration tests or mocking infrastructure present
- Jupyter notebooks in `investigations/` for manual API testing

### .gitignore Highlights

**Always ignored**:
- `google_token/*.json` (OAuth tokens)
- `local.settings.json` (local configuration)
- `__pycache__/`, `.pytest_cache/` (build artifacts)
- `.venv/`, `venv/` (virtual environments)
- `__blobstorage__/`, `__queuestorage__/` (Azurite storage)

## Development Workflow

### Making Code Changes

1. **ALWAYS install dependencies first** if starting fresh:
   ```bash
   pip install -r requirements_local.txt
   ```

2. **Make minimal changes** to the relevant files

3. **Validate syntax immediately**:
   ```bash
   python3 -m py_compile <changed_file.py>
   ```

4. **Run tests after each change**:
   ```bash
   python3 -m pytest tests/ -v
   ```

5. **Verify imports work**:
   ```bash
   python3 -c "import function_app"
   ```

### Common Pitfalls and Workarounds

**Azure Functions Core Tools not available**: 
- `func` command will not work outside dev container
- Use dev container for local testing
- In standard environment, rely on syntax validation and unit tests

**Secrets and Authentication**:
- Functions that call Azure Key Vault or external APIs will fail without proper credentials
- Use `local.settings.json` (not in repo) for local development
- Mock secret retrieval in tests if adding new secret-dependent code

**Event Grid Bindings**:
- Output bindings (e.g., `@task_output_binding()`) only work when deployed to Azure
- Test by validating the function compiles and the event models serialize correctly

**Import Paths**:
- All imports use absolute paths from repository root (e.g., `from shared.secrets import ...`)
- Python path is configured to include repository root
- Do not use relative imports

### Adding New Functions

1. Create function in appropriate directory (`infrastructure/` or `usecases/`)
2. Import function in `function_app.py` at the top (do not modify the `app` line)
3. Use decorators: `@app.timer_trigger()`, `@app.route()`, or `@app.event_grid_trigger()`
4. Add tests in `tests/` directory
5. Update this documentation if adding a new major feature

### Debugging Tips

- Use `logging.info()` / `logging.error()` for output (configured by Azure Functions runtime)
- Check `investigations/` directory for example API usage in Jupyter notebooks
- Review `notes/dev_setup.md` for Azure portal configuration details
- Event Grid subscriptions are configured in Azure portal, not in code

## Continuous Integration

**No CI/CD pipeline is currently configured**. There are no GitHub Actions workflows or automated builds. Validation steps:

1. Run tests manually: `python3 -m pytest tests/ -v`
2. Validate syntax: `python3 -m py_compile function_app.py`
3. Check imports: `python3 -c "import function_app"`

## Key Facts for Efficient Work

**TRUST THESE INSTRUCTIONS**: The information here has been validated. Only search the codebase if:
- You need to understand implementation details of a specific function
- The instructions are incomplete or incorrect for your specific task
- You're adding a new type of functionality not covered here

**Before exploring with grep/find/search**:
1. Check this file first for relevant information
2. Use the directory structure section to navigate directly to files
3. Remember: most utility functions are in `shared/`, integrations in `infrastructure/`, business logic in `usecases/`

**Time-saving facts**:
- Tests take < 1 second, run them frequently
- Dependency installation takes 30-60 seconds
- No linting tools to configure or run
- No build step required (Python is interpreted)
- Focus changes on `.py` files; configuration files rarely need modification

**Architecture patterns used**:
- Pydantic models for data validation and JSON parsing
- Azure Functions decorators for function registration
- Event Grid for async communication between functions
- Dependency injection of services (e.g., `TaskService`, `MangaUpdateService`)
- Separation of concerns: Functions (entry points) → Services (logic) → Models (data)
