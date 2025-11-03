## General coding & architecture guidelines for Copilot / automation

When producing code or wiring components in this repository, follow these rules by default unless the user explicitly requests otherwise:

- Filenames: choose descriptive filenames so they are easy to locate with the editor "Go to file" (avoid generic names like `service.py`).
- Imports: always use absolute imports from the repository root (for example: `infrastructure.google.task.TaskService`).
- Package files: do not create `__init__.py` files unless required; prefer absolute imports and minimal packaging.
- Documentation: do not add docstrings or explanatory comments unless explicitly requested by the user.
- Typing: be type-strict. Use modern Python union syntax (e.g. `str | None`) instead of `Optional[str]`.
- Data models: prefer `pydantic` models for external-facing payloads and secret parsing to get automatic validation and datetime parsing.
- Naming: use clear, domain-specific names (e.g. `TaskService.py`, `TaskModels.py`, `TaskSchemas.py`).
- Tests: do not run tests or create test artifacts unless the user asks for them. Create tests only when requested.
- Edits: prefer minimal, targeted edits. Avoid reformatting unrelated files.
- Verification: do not perform checks like importing modules.
- Security: do not exfiltrate secrets. Use existing secret helpers (`shared.secrets`) and Key Vault. When adding code that accesses secrets, rely on `DefaultAzureCredential` and `SecretClient` patterns already in the repo.
- Azure patterns: when creating Azure Functions, mirror the repository patterns (see `infrastructure/telegram` for examples): use `function_app.app` decorators, event grid output bindings in helper modules, and register functions by importing them in `function_app.py`.
- when given feedback about code style or architecture, add to this list in a concise manner.

If a repo-wide convention isn't clear from context, infer the smallest reasonable assumption and proceed; call out assumptions in your change summary.
