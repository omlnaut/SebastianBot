# Dependency Management

This project uses [Poetry](https://python-poetry.org/) for dependency management while maintaining compatibility with Azure Functions deployment via `requirements.txt`.

## Poetry Setup in Devcontainer

The devcontainer automatically installs Poetry and all dependencies when built. The setup includes:

- Poetry and the `poetry-plugin-export` plugin (for generating `requirements.txt`)
- Virtual environments are disabled (`virtualenvs.create false`) since we're inside a container
- All dependencies (including dev dependencies) are installed via `poetry install`

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

After adding dependencies, both `pyproject.toml` and `poetry.lock` will be updated automatically.

## Version Constraints

Dependencies use caret (`^`) version constraints:
- `^1.24` allows versions `>=1.24.0` and `<2.0.0`
- This allows minor and patch updates while preventing breaking major version changes

## Deploying to Azure

Azure Functions requires a `requirements.txt` file for deployment. Before deploying:

1. **Export dependencies to requirements.txt:**
   ```bash
   poetry export -f requirements.txt --output requirements.txt --without-hashes
   ```

2. **Commit the updated `requirements.txt`**

3. **Deploy to Azure** via the Azure Functions extension

> **Note:** Only production dependencies are exported. Dev dependencies (pytest, ipykernel, etc.) are not included in the deployment.

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Poetry configuration and dependency definitions |
| `poetry.lock` | Locked versions for reproducible builds |
| `requirements.txt` | Generated file for Azure Functions deployment |

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
```
