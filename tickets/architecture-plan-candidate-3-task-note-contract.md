# Ticket: Candidate 3 Deepening Plan — Delivery-ready Task note contract Module

## Context
Current Delivery Notification and CheckParcelReceived UseCase Modules share an implicit Task note contract via free-text formatting + regex parsing.

This is a shallow setup:
- Interface invariants (Tracking Number line format, Task Tag presence) are implicit.
- Implementation details leak across Module seams.
- Tests do not center on the Interface as the test surface.

## Goal
Deepen this area by introducing one Task note contract Module with a clear Interface, then attach two Adapter implementations at the seam:
1. Delivery Notification writer side
2. CheckParcelReceived reader side

This should improve Locality (one place to change grammar) and Leverage (callers stop hand-building/parsing note text).

---

## Commit Plan (minimal, low-risk)

### Commit 1 — Introduce deep Module (no behavior change yet)

#### Add
- `sebastian/domain/delivery_ready_task_note.py`
  - `DeliveryReadyTaskNote.from_pickup_data(...)`
  - `DeliveryReadyTaskNote.from_text(...)`
  - `DeliveryReadyTaskNote.to_text(...)`

#### Add tests
- `tests/unit_tests/domain/test_delivery_ready_task_note.py`
  - round-trip encode/decode
  - missing Tracking Number
  - Task Tag detection
  - uppercase normalization

#### Outcome
A single deep Module defines the Interface for the Task note contract, without integrating into existing UseCase flow yet.

---

### Commit 2 — Use contract Module in Delivery Notification handler (Adapter 1)

#### Change
- `sebastian/usecases/features/delivery_ready/handler.py`
  - replace manual note string assembly in `_map_to_create_task`
  - use `DeliveryReadyTaskNote.from_pickup_data(...).to_text()`

#### Add/adjust tests
- `tests/unit_tests/usecases/test_delivery_ready_retry.py`
  - assert `CreateTask.notes` follows contract output (or parse back using `from_text`)

#### Outcome
Writer-side Adapter now uses the seam.

---

### Commit 3 — Use contract Module in CheckParcelReceived handler (Adapter 2)

#### Change
- `sebastian/usecases/features/check_parcel_received/handler.py`
  - remove regex Tracking Number extraction path
  - parse notes via `DeliveryReadyTaskNote.from_text(task.notes)`
  - use parsed `tracking_number` and Task Tag facts

#### Add tests
- `tests/unit_tests/usecases/test_check_parcel_received.py` (new if missing)
  - valid contract note → Task Completion Side Effect
  - Task Tag without Tracking Number → skipped safely
  - malformed notes → safe behavior, no crash

#### Outcome
Reader-side Adapter now uses the same seam. Two Adapter setup makes this a real seam.

---

### Commit 4 — Cleanup + guardrails

#### Cleanup
- remove dead helpers / constants in `check_parcel_received/handler.py`
- optional note in docs/comments clarifying contract ownership by the new Module

#### Add guard test
- cross-flow test proving Delivery Notification output is parseable by CheckParcelReceived parser

#### Outcome
Locality and Leverage are locked in; regressions toward implicit contract are less likely.

---

## Acceptance Criteria
- Delivery-ready Task note format is owned by one Module.
- Delivery Notification and CheckParcelReceived both depend on that Interface.
- Regex-based Tracking Number extraction is removed from CheckParcelReceived.
- Tests validate round-trip contract behavior and malformed-input safety.

## Verification
- Run: `pytest tests/unit_tests`
- Ensure existing UseCase tests still pass after integration.
