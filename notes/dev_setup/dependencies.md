# Dependency Management

This project uses [Poetry](https://python-poetry.org/) for dependency management while maintaining compatibility with Azure Functions deployment via `requirements.txt`.

## Poetry Setup in Devcontainer

The devcontainer automatically installs Poetry and all dependencies when built. The setup includes:

- Poetry and the `poetry-plugin-export` plugin (for generating `requirements.txt`)
- Virtual environments are disabled (`virtualenvs.create false`) since we're inside a container
- All dependencies (including dev dependencies) are installed via `poetry install`
- Pre-commit hooks are installed automatically via `postCreateCommand`

No additional setup is needed when using the devcontainer.

## Adding New Dependencies

### Production dependencies
```bash
poetry add <package-name>
```

Example:
```bash
poetry add requests
```

### Development dependencies
```bash
poetry add --group dev <package-name>
```

Example:
```bash
poetry add --group dev black
```

### Test dependencies
```bash
poetry add --group test <package-name>
```

Example:
```bash
poetry add --group test pytest-mock
```

After adding dependencies, both `pyproject.toml` and `poetry.lock` will be updated automatically.

## Version Constraints

Dependencies use caret (`^`) version constraints:
- `^1.24` allows versions `>=1.24.0` and `<2.0.0`
- This allows minor and patch updates while preventing breaking major version changes

## Deploying to Azure

Azure Functions requires a `requirements.txt` file for deployment.

### Automatic Export (Pre-commit Hook)

A pre-commit hook automatically exports `requirements.txt` whenever `pyproject.toml` or `poetry.lock` changes. This ensures the requirements file is always in sync when you commit dependency changes.

The hook runs:
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### CI Validation

The GitHub Actions workflow includes a check that validates `requirements.txt` is up-to-date with `pyproject.toml`. If the check fails, it means the `requirements.txt` file needs to be regenerated.

**To fix a failing check:**
1. **Recommended:** Simply commit your changes. The pre-commit hook will automatically update `requirements.txt` for you.
2. **Alternative:** Manually run the export command (see below).

### Manual Export

If needed, you can manually export:
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

> **Note:** Only production dependencies are exported. Dev and test dependencies (pytest, ipykernel, etc.) are not included in the deployment.

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Poetry configuration and dependency definitions |
| `poetry.lock` | Locked versions for reproducible builds |
| `requirements.txt` | Generated file for Azure Functions deployment |
| `.pre-commit-config.yaml` | Pre-commit hook configuration |

## Useful Commands

```bash
# Install all dependencies
poetry install

# Run tests
poetry run pytest

# Update all dependencies to latest allowed versions
poetry update

# Show outdated packages
poetry show --outdated

# Run pre-commit hooks manually
pre-commit run --all-files
```
