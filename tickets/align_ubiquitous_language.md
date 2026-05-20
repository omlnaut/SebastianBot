# Ticket: Align Codebase with Ubiquitous Language

## Description
The codebase currently uses several terms that are ambiguous or inconsistent with the agreed-upon domain language. This ticket tracks the necessary renames and structural changes to bring the implementation in line with `UBIQUITOUS_LANGUAGE.md`.

## Proposed Changes

### 1. Side Effects & Events
- **Rename** `BaseActorEvent` to `SideEffect` across the entire codebase.
- **Rename** `sebastian/domain/side_effects.py` and references to reflect this.
- **Update** `EVENT_MAP` in `cloud/functions/side_effects/shared.py` to use `SIDE_EFFECT_MAP` (or similar).

### 2. Task Management
- **Rename** `TaskLabels` enum to `TaskTags`.
- **Rename** variable/attribute names from `label` to `tag` where they refer to the internal Task tagging system (distinguish from Gmail labels).

### 3. Bibo Domain
- **Move** `BookLendingInfo` from `sebastian/usecases/features/bibo_lending_sync/protocols.py` to `sebastian/domain/bibo.py`.
- **Rename** `BookLendingInfo` to `Lending`.
- **Rename** variables named `account` to `bibo_account` in UseCase handlers and dependency injection logic (e.g., in `cloud/dependencies/`).

### 4. Shared Domain Entities
- **Create** `sebastian/domain/shared.py`.
- **Move** `TimeRange` from `sebastian/usecases/shared/dates.py` to `sebastian/domain/shared.py`.
- **Move** `DateFilter` from `sebastian/domain/date_filter.py` to `sebastian/domain/shared.py` (optional, for consolidation).

### 5. Logistics (Delivery & Returns)
- **Rename** `tracking_id` to `tracking_number` in `CheckParcelReceived` handler and related logic to match `PickupData`.
- **Standardize** terminology in logs and comments to use **Delivery Notification** and **Return Notification**.

### 6. Mietplan
- **Rename** `Folder` to `MietplanFolder` and `File` to `MietplanFile` in `sebastian/domain/mietplan.py` to avoid collisions with generic types.

## Verification
- Run all unit tests: `pytest tests/unit_tests`
- Verify that `tests/unit_tests/test_event_map.py` still correctly registers all subclasses (after rename).
- Ensure no broken imports in `cloud/functions/`.

## Reference
See `UBIQUITOUS_LANGUAGE.md` for the canonical definitions of these terms.
