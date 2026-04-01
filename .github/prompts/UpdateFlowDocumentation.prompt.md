---
agent: agent
---
# Update Feature Usecase Flow Documentation

Run this instruction before merging a PR to keep `.github/instructions/feature_usecase_flow.instructions.md` in sync with the current state of the codebase.

## Task

Review the code changes introduced by the current PR and update `.github/instructions/feature_usecase_flow.instructions.md` so it accurately reflects any architectural changes.

## Steps

1. **Get the PR diff**
   - Use `git diff origin/main...HEAD` to see all changes introduced by this PR.
   - Focus on files in:
     - `sebastian/usecases/features/`
     - `sebastian/domain/`
     - `sebastian/clients/`
     - `cloud/functions/features/`
     - `cloud/functions/infrastructure/`
     - `cloud/functions/side_effects/`
     - `cloud/dependencies/`
     - `function_app.py`
     - `cloud/functions/TriggerTimes.py`

2. **Identify what changed architecturally**
   Only update the flow doc when the PR introduces or changes one of the following:
   - The overall flow between layers (timer → handler → AllActor → EventGrid → side effects)
   - The structure or conventions of feature usecase files (`handler.py`, `protocols.py`, `parsing.py`, `__init__.py`)
   - Domain model location or patterns (`sebastian/domain/`)
   - How `AllActor` fields map to side effects
   - How secrets are managed (`SecretKeys`, `get_secret`)
   - How client resolvers are wired (`cloud/dependencies/clients.py`)
   - How usecase resolvers are written (`cloud/dependencies/usecases.py`)
   - `TriggerTimes` / Azure Function structure
   - `function_app.py` registration pattern
   - EventGrid infrastructure or side-effect function patterns
   - The side-effect usecase structure (`sebastian/usecases/side_effects/`) or `perform_usecase_from_eventgrid` behaviour

   Skip updates for:
   - New usecase implementations that follow the existing pattern unchanged
   - Bug fixes that do not affect architecture
   - Test-only changes
   - Documentation-only changes

3. **Update the flow doc**
   For each architectural change identified in step 2:
   - Locate the relevant section in `feature_usecase_flow.instructions.md`
   - Update the description, code example, or checklist item to match the new pattern
   - If a new architectural concept is introduced that has no section yet, add a new section in the appropriate place
   - If an existing pattern was removed or replaced, remove or rewrite the corresponding section
   - Keep the canonical example consistent: if `delivery_ready` is updated, reflect that throughout the doc; otherwise keep it as-is

4. **Do not change**
   - The overall document structure (sections, heading hierarchy) unless the architecture genuinely changed
   - The `delivery_ready` worked example unless that usecase itself was modified in the PR
   - Wording unrelated to what changed in the PR
