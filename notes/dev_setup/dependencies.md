# Dependency Management

This project uses [uv](https://github.com/astral-sh/uv) for dependency management while maintaining compatibility with Azure Functions deployment via `requirements.txt`.

## uv Setup in Devcontainer

The devcontainer automatically installs uv and all dependencies when built. The setup includes:

- uv is installed from the official Docker image
- All dependencies (including dev and test dependencies) are installed via `uv pip install`
- Pre-commit hooks are installed automatically via `postCreateCommand`

No additional setup is needed when using the devcontainer.

## Adding New Dependencies

### Production dependencies
```bash
uv add <package-name>
```

Example:
```bash
uv add requests
```

### Development dependencies
```bash
uv add --dev <package-name>
```

Example:
```bash
uv add --dev black
```

### Test dependencies
```bash
uv add --optional test <package-name>
```

Example:
```bash
uv add --optional test pytest-mock
```

After adding dependencies, both `pyproject.toml` and `uv.lock` will be updated automatically.

## Version Constraints

Dependencies use standard PEP 440 version constraints:
- `>=1.24,<2.0` allows versions `>=1.24.0` and `<2.0.0`
- This allows minor and patch updates while preventing breaking major version changes

## Deploying to Azure

Azure Functions requires a `requirements.txt` file for deployment.

### Automatic Export (Pre-commit Hook)

A pre-commit hook automatically exports `requirements.txt` whenever `pyproject.toml` or `uv.lock` changes. This ensures the requirements file is always in sync when you commit dependency changes.

The hook runs:
```bash
uv pip compile pyproject.toml -o requirements.txt
```

### CI Validation

The GitHub Actions workflow includes a check that validates `requirements.txt` is up-to-date with `pyproject.toml`. If the check fails, it means the `requirements.txt` file needs to be regenerated.

**To fix a failing check:**
1. **Recommended:** Simply commit your changes to `uv.lock` or `pyproject.toml`. The pre-commit hook will automatically update `requirements.txt` for you.
2. **Alternative:** Manually run the export command (see below).

### Manual Export

If needed, you can manually export:
```bash
uv pip compile pyproject.toml -o requirements.txt
```

> **Note:** Only production dependencies are exported. Dev and test dependencies (pytest, ipykernel, etc.) are not included in the deployment.

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project configuration and dependency definitions (PEP 621 format) |
| `uv.lock` | Locked versions for reproducible builds |
| `requirements.txt` | Generated file for Azure Functions deployment |
| `.pre-commit-config.yaml` | Pre-commit hook configuration |

## Useful Commands

```bash
# Install all dependencies
uv sync

# Install only production dependencies
uv pip install --system -e .

# Install with optional dependencies (e.g., test)
uv pip install --system -e ".[test]"

# Run tests
uv run pytest

# Update all dependencies to latest allowed versions
uv lock --upgrade

# Show outdated packages
uv pip list --outdated

# Run pre-commit hooks manually
pre-commit run --all-files
```
