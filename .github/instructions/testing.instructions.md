# Testing Guidelines

This document outlines the testing strategy and guidelines for the SebastianBot project.

## Overview

The project follows a clean architecture with two main layers:
- **sebastian/** - Application layer (business logic, clients, usecases, shared utilities)
- **cloud/** - Infrastructure layer (Azure functions, dependencies, helpers)

Testing primarily focuses on the `sebastian/` application layer, as this contains testable business logic. The `cloud/` layer is excluded from unit testing due to its reliance on Azure infrastructure.

## What to Test

### Priority 1: Shared Utilities (`sebastian/shared/`)
- Pure functions like date utilities, result handling
- These have no external dependencies and are easy to test
- Tests should cover edge cases and different input scenarios

### Priority 2: Parsing/Transformation Logic
- Each usecase may have parsing or transformation logic (e.g., `parsing.py`)
- Test with sample data files when parsing external formats (HTML, JSON, etc.)
- Store test fixtures in the same directory as the test file

### Priority 3: Service Logic
- Test service orchestration logic using mocked clients
- Use dependency injection to inject mock clients
- Focus on testing business rules, not client interactions

### Priority 4: Architecture Constraints
- Ensure `sebastian/` doesn't import from `cloud/` (existing test in `test_imports.py`)
- These tests prevent architectural violations

### Not Tested (For Now)
- **cloud/** layer (Azure Functions, infrastructure)
- Client implementations (they interact with external services)
- Notebooks (investigation/showcase purposes only)

## Test Structure

Tests are organized by type:

```
tests/
├── unit_tests/                # Unit tests for isolated logic
│   ├── test_dates.py          # Tests for sebastian/shared/dates.py
│   ├── test_imports.py        # Architecture constraint tests
│   └── usecases/
│       └── DeliveryReady/
│           ├── test_parsing.py    # Tests for parsing logic
│           └── dhl_test_mail.html # Test fixture
└── integration_tests/         # Integration tests with external services
    └── test_gemini.py         # Tests for Gemini API integration
```

**Unit Tests** (`tests/unit_tests/`):
- Tests for pure functions, parsing logic, and business rules
- No external service dependencies
- Fast execution
- Mirror source code structure

**Integration Tests** (`tests/integration_tests/`):
- Tests that call real external services
- Require credentials (via resolvers)
- Slower execution
- Organized by client/service being tested
- As test files grow, split them by functionality:
    - Create a directory for the client (e.g., `gmail/`)
    - Split into focused test files (e.g., `test_fetch_mails.py`, `test_labels.py`, `test_pdf_attachments.py`)
    - Add `conftest.py` for shared fixtures
    - Example: `test_gmail.py` → `gmail/test_fetch_mails.py`, `gmail/test_labels.py`, etc.

### Naming Conventions
- Test files: `test_{module_name}.py`
- Test functions: `test_{function_name}_{scenario}`
- Test fixtures: Placed in the same directory as the test file

### Test File Template

```python
from sebastian.{module} import {function_or_class}


def test_{function_name}_{scenario}():
    # Arrange
    input_data = ...
    
    # Act
    result = function_or_class(input_data)
    
    # Assert
    assert result == expected_value


def test_{function_name}_{edge_case}():
    # Test edge cases and error conditions
    ...
```

## Running Tests

### Local Development

```bash
# Install test dependencies (using Poetry)
poetry install --with test

# Run all tests (unit + integration)
poetry run pytest

# Run only unit tests (fast, no external dependencies)
poetry run pytest tests/unit_tests

# Run only integration tests (requires credentials)
poetry run pytest tests/integration_tests

# Run tests with coverage
poetry run pytest tests/unit_tests --cov=sebastian --cov-report=html

# Run specific test file
poetry run pytest tests/unit_tests/test_dates.py

# Run tests matching a pattern
poetry run pytest -k "test_parsing"
```

### Configuration

Test configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

## GitHub Actions Workflow

Tests run automatically on pull requests and pushes to main. The workflow is configured in `.github/workflows/tests.yml`.

**Note**: Only **unit tests** run in CI (`tests/unit_tests`) to avoid requiring credentials and keep CI fast. Integration tests should be run locally before merging.

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest
          virtualenvs-create: true
          virtualenvs-in-project: true
      
      - name: Install dependencies
        run: poetry install --only main,test
      
      - name: Run tests
        run: poetry run pytest tests/unit_tests --cov --cov-report=xml
```

## Coverage Reporting

### Coverage Scope
Coverage is measured only for these directories (configured in `pyproject.toml`):
- `sebastian/infrastructure/`
- `sebastian/shared/`
- `sebastian/usecases/`

Clients are excluded since they primarily interact with external services.

### Local Coverage Report
```bash
poetry run pytest --cov=sebastian --cov-report=html
open htmlcov/index.html
```

### Coverage Targets
- Focus on increasing coverage for `sebastian/shared/` and parsing logic
- No strict coverage percentage requirements initially
- Prioritize meaningful tests over coverage metrics

## Refactoring for Testability

### Current State
The project is already reasonably testable due to:
- Clean separation between `sebastian/` and `cloud/` layers
- Dependency injection in services (clients are injected via `__init__`)
- Extracted parsing/transformation logic in separate modules

### Recommended Improvements

1. **Add pytest configuration**
   - Use `[tool.pytest.ini_options]` section in `pyproject.toml`
   - Set `pythonpath = ["."]` to avoid PYTHONPATH environment variable

2. **Create test fixtures module**
   - For commonly used test data (e.g., mock Result objects)
   - Place in `tests/conftest.py` for shared fixtures

3. **Mock external services in service tests**
   - Services use protocols (from `sebastian/protocols/`) for dependency injection
   - Use `unittest.mock` or `pytest-mock` to create mock implementations of protocols
   - Focus on testing service logic, not client implementations

4. **Example refactoring for service testing**:
   ```python
   # tests/usecases/DeliveryReady/test_service.py
   from unittest.mock import Mock
   from sebastian.usecases.DeliveryReady.service import DeliveryReadyService

   def test_service_returns_ready_deliveries():
       # Arrange
       mock_client = Mock()
       mock_client.fetch_mails.return_value = [...]
       service = DeliveryReadyService(gmail_client=mock_client)
       
       # Act
       result = service.get_recent_dhl_pickups()
       
       # Assert
       assert result.item is not None
   ```

## Instructions for Adding Tests

When developing new features, follow these steps:

### For New Shared Utilities
1. Create tests in `tests/test_{module_name}.py`
2. Test all public functions
3. Include edge cases and error scenarios
4. Run tests locally before committing

### For New Usecases
1. Create test directory: `tests/usecases/{UseCase}/`
2. Add `test_parsing.py` if parsing logic exists
3. Add `test_service.py` for service logic (with mocked clients)
4. Include test fixtures (sample data files) in the same directory

### For New Clients
- Generally not unit tested (external service interactions)
- Use investigation notebooks for manual testing
- If client has complex transformation logic, extract to testable modules

### Test Best Practices

**Path Resolution in Tests:**
- **Never hardcode absolute paths** (e.g., `/workspaces/SebastianBot`)
- Use dynamic path resolution: `Path(__file__).resolve().parents[N]`
- This ensures tests work in both local dev containers and CI environments
- Example:
  ```python
  # ✅ Good - dynamic
  ROOT_DIR = Path(__file__).resolve().parents[1]  # test file is at <repo>/tests/
  
  # ❌ Bad - hardcoded
  ROOT_DIR = Path("/workspaces/SebastianBot")
  ```

**Parametrized Tests:**
- Precompute parameter lists to avoid "empty parameter set" skips
- Add guard tests to ensure parameter lists are not empty
- Example:
  ```python
  # Precompute list
  _FILES = [str(p) for p in some_dir.rglob("*.py")]
  
  # Guard test
  def test_files_found():
      assert len(_FILES) > 0, "No files found"
  
  # Use precomputed list
  @pytest.mark.parametrize("file", _FILES)
  def test_something(file):
      ...
  ```

**CI Reliability:**
- Tests that fail locally must also fail in CI (no silent skips)
- Check CI logs if tests show as "skipped" unexpectedly
- Common causes: hardcoded paths, missing environment setup

### Test Checklist for PRs
- [ ] Tests added for new functionality
- [ ] All tests pass locally (`poetry run pytest`)
- [ ] Test names follow naming conventions
- [ ] Edge cases considered
- [ ] No hardcoded paths in test files
- [ ] Parametrized tests have guard tests

## Dependencies

Test dependencies are in `pyproject.toml` under `[tool.poetry.group.test.dependencies]`:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
