# Email Processing Migration Plan

## Goal
Move email consumption from per-usecase unread/time-window polling to a central mail-check flow:
- Fetch emails after a cutoff date.
- Skip emails already marked with Processed label.
- Run matching sub-usecases on each unprocessed email.

## Final Decisions
1. Scope (phase 1): migrate delivery_ready and return_tracker only.
2. Multi-match behavior: execute all matching sub-usecases for a mail.
3. Matching strategy: broad central fetch; matching happens inside each sub-usecase `check_if_mail_matches`.
4. Side-effect ownership: sub-usecases remain normal usecases and decide labels themselves.
5. Transient failures: default is retry later (do not set Processed).
6. Terminal failures: no global default; each sub-usecase decides behavior.
7. Retry horizon: no shared horizon in central checker.
8. Cutoff strategy: fixed configured start datetime.
9. Processed label: hardcoded in `GmailLabel` enum.
10. Rollout: direct cutover (no shadow/dual-run period).
11. Trigger cadence: run central mail-check every 10 minutes.
12. Cutoff value: set at deployment time to first go-live timestamp.
13. Sub-usecase list ownership: define in dependency resolver/composition root, not in central handler.
14. Unmatched mails: central handler marks as Processed.
15. Matched but no side-effects: do not central-mark as Processed; preserve sub-usecase retry semantics.

## Migration Steps

### (x) 1) Add Processed label support
0. Add `get_labels` to gmail client to easily get existing labels and their ids.
1. Add `Processed` to `sebastian/domain/gmail.py` enum (`GmailLabel`).
2. Keep existing labels unchanged.
3. Test: extend Gmail label integration tests to verify add/remove for Processed.

### 2) Introduce central mail-check usecase
1. Create new feature usecase package (for example `sebastian/usecases/features/mail_check/`).
2. Define a sub-usecase contract:
   - `check_if_mail_matches(mail) -> bool`
   - `handle_mail(mail) -> Sequence[SideEffect]`
3. Implement central handler flow:
   - Fetch all mails after cutoff date.
   - Filter out mails already containing Processed label id.
   - For each remaining mail, execute all matching sub-usecases.
   - Concatenate and return side effects.
   - If no sub-usecase matches a mail, central handler adds Processed label side effect for that mail.
   - If at least one sub-usecase matches, central handler does not enforce Processed; sub-usecases own label policy.
4. Unit tests:
   - Skips already-processed mails.
   - Executes all matching sub-usecases for same mail.
   - Marks unmatched mails as Processed.
   - Does not centrally mark Processed when at least one sub-usecase matched but returned no side effects.
   - Deterministic side-effect ordering.

### 3) Refactor delivery_ready into a mail sub-usecase
1. Keep parsing and transient retry behavior, but process provided mail object instead of querying Gmail internally.
2. Implement `check_if_mail_matches` based on current sender/subject semantics.
3. Success path should include Processed label side effect.
4. Transient failures should not include Processed label.
5. Terminal behavior remains local to this sub-usecase.
6. Tests: migrate existing delivery_ready retry tests to new mail-level sub-usecase tests.

### 4) Refactor return_tracker into a mail sub-usecase
1. Keep parsing and retry behavior, but process provided mail object.
2. Implement `check_if_mail_matches` with current sender/subject/content criteria.
3. Success path should include Processed label side effect.
4. Transient failures should not include Processed label.
5. Terminal behavior remains local to this sub-usecase.
6. Tests: migrate existing return_tracker retry tests to new mail-level sub-usecase tests.

### 5) Wire dependencies and timer trigger
1. Add resolver for central mail-check handler in `cloud/dependencies/usecases.py`, and define ordered phase-1 sub-usecases list there: delivery_ready, return_tracker.
2. Add timer function (for example `cloud/functions/features/mail_check_function.py`).
3. Set `TriggerTimes.MailCheck` to every 10 minutes (`*/10 * * * *`).
4. Register function import in `function_app.py`.
5. Tests: update function/event map tests to include new trigger path.

### 6) Direct cutover from old timers
1. Disable delivery_ready and return_tracker timer registrations in `function_app.py`.
2. Keep old code files temporarily for rollback safety, but do not register old triggers.
3. Verify only central mail-check handles these flows.

### 7) Configure go-live cutoff at deployment
1. Set fixed cutoff datetime to deployment go-live instant.
2. Ensure Processed label id is correct before deploy.
3. Deploy and validate first cycle behavior in logs.

### 8) Post-cutover validation
1. Add/verify structured logs:
   - fetched mail count
   - skipped as processed count
   - per-sub-usecase match count
   - per-sub-usecase success/transient/terminal counts
2. Smoke-test one or more timer cycles.
3. Manually verify that processed mails are not reprocessed.

## Test Execution Order
1. New central + sub-usecase unit tests.
2. Existing unit regression suite.
3. Gmail integration tests (especially label tests).
4. Function wiring/event map tests.
5. Post-deploy smoke validation.

## Out of Scope (for this migration)
1. winsim migration (phase 2).
2. Sophisticated retry coordination when multiple sub-usecases match and only a subset fail.
