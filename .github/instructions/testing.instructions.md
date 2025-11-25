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

Tests mirror the source code structure:

```
tests/
├── test_dates.py              # Tests for sebastian/shared/dates.py
├── test_imports.py            # Architecture constraint tests
└── usecases/
    └── DeliveryReady/
        ├── test_parsing.py    # Tests for parsing logic
        └── dhl_test_mail.html # Test fixture
```

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
# Install test dependencies
pip install -r requirements_local.txt

# Run all tests
PYTHONPATH=. pytest

# Run tests with coverage
PYTHONPATH=. pytest --cov=sebastian --cov-report=html

# Run specific test file
PYTHONPATH=. pytest tests/test_dates.py

# Run tests matching a pattern
PYTHONPATH=. pytest -k "test_parsing"
```

### Configuration

Add `pytest.ini` or `pyproject.toml` for consistent test configuration:

```ini
# pytest.ini
[pytest]
pythonpath = .
testpaths = tests
addopts = -v --tb=short
```

## GitHub Actions Workflow

Tests run automatically on pull requests and pushes to main. Create `.github/workflows/tests.yml`:

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
      
      - name: Install dependencies
        run: pip install -r requirements_local.txt
      
      - name: Run tests
        run: pytest --cov=sebastian --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          fail_ci_if_error: false
```

## Coverage Reporting

### Local Coverage Report
```bash
PYTHONPATH=. pytest --cov=sebastian --cov-report=html
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
   - Create `pytest.ini` or use `pyproject.toml` section
   - Set `pythonpath = .` to avoid PYTHONPATH environment variable

2. **Create test fixtures module**
   - For commonly used test data (e.g., mock Result objects)
   - Place in `tests/conftest.py` for shared fixtures

3. **Mock external services in service tests**
   - Use `unittest.mock` or `pytest-mock` to mock client dependencies
   - Focus on testing service logic, not client implementations

4. **Example refactoring for service testing**:
   ```python
   # tests/usecases/DeliveryReady/test_service.py
   from unittest.mock import Mock
   from sebastian.usecases.DeliveryReady.service import DeliveryReadyService

   def test_service_returns_ready_deliveries():
       # Arrange
       mock_client = Mock()
       mock_client.get_emails.return_value = [...]
       service = DeliveryReadyService(client=mock_client)
       
       # Act
       result = service.get_ready_deliveries()
       
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

### Test Checklist for PRs
- [ ] Tests added for new functionality
- [ ] All tests pass locally (`PYTHONPATH=. pytest`)
- [ ] Test names follow naming conventions
- [ ] Edge cases considered

## Dependencies

Test dependencies are in `requirements_local.txt`:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
