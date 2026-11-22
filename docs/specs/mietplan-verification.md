# Mietplan verification items (spec §5)

Status of the five verification items in `docs/specs/mietplan-cli-session.md` §5,
recorded honestly for the `seadepot` / resync work (#125–#129). "Measured" means a
real request or run was made; "assumed" means the code relies on the stated behaviour
but this machine could not execute it.

This machine has **no portal credentials** (`SEAMIETPLAN_CREDENTIALS`), **no Google
Drive token or Key Vault access**, and **no Azure login or deployment access**. The
integration suite (`tests/integration_tests/mietplan/`) is therefore written but
skips here; it is the proof that would settle V2–V5 on a credentialed dev machine.

| Item | Question | Status |
| --- | --- | --- |
| **V1** | What does an expired/rejected session return from `getFolders`? | **Measured** (2026-11-22) |
| **V2** | Real `filepath` shapes and `html.unescape` / URL-join fidelity | **Assumed**, live test written |
| **V3** | Does `files().update(media_body=…)` keep id, parents and sharing? | **Assumed**, live test written |
| **V4** | Are duplicate-name Drive lookups deterministic? | **Resolved by rule**, not measured |
| **V5** | Walk cost and the Functions execution timeout | **Estimated/recorded**, not measured |

## V1 — rejected session response (measured)

Measured on **2026-11-22** with real network requests against `mietplan-dresden.de`,
not a fake session:

- An unauthenticated `getFolders` request returns **HTTP 403** with an **empty
  `text/html` body**.
- A deliberately rejected login through the installed `seadepot` CLI produces the
  same signal; the CLI reports `{"kind":"auth","message":"login was rejected: the
  portal answered HTTP 403 for folder ac4do35ktgfi79j8ids35om8udm"}`, exit 1, never
  an empty file list.

`_verify_session.verify_session` therefore keys off the real signal: status `401`/
`403`, or a successful response whose body is not a JSON object, is
`MietplanAuthError`. Transport failures and 5xx answers are not auth errors; they
stay `kind: api`. Unit coverage is in
`tests/unit_tests/clients/mietplan/test_verify_session.py` (including a 403 with an
empty HTML body), but the fact being encoded came from the live requests above.

## V2 — real `filepath` values (assumed)

**Assumed:** portal `filepath` values (umlauts, spaces, `&`, parentheses, possible
query parameters or percent-encoding) round-trip through `html.unescape` for display
and through `base + download_path` for the actual download.

**What would prove it:** `tests/integration_tests/mietplan/test_download_live.py::
test_download_writes_a_real_document_under_out` downloads a document found by a
real walk and asserts non-empty bytes of the reported size. A systematic catalogue of
`filepath` forms is not part of that test, so unusual encodings remain unproven.

## V3 — in-place update semantics (assumed)

**Assumed:** `files().update(fileId=…, media_body=…, fields="id")` with **no metadata
body** keeps the file id, its parents and its sharing, and completes for a realistic
invoice-sized PDF. The implementation is
`sebastian/clients/google/drive/client/replace_file.py`.

**What would prove it:** `tests/integration_tests/mietplan/test_upsert.py::
test_upsert_replaces_the_same_file_id_and_keeps_it_findable` asserts the id survives
the update and remains findable; parents and sharing would need a manual look in the
Drive UI after that run.

## V4 — duplicate-name lookup determinism (resolved by rule)

**Assumption:** Drive does not make a path lookup unambiguous when a folder or file
name already exists twice under the same parent (the old always-create bug left such
duplicates). Nothing has cleaned them up, and this code never deletes (D13).

**Resolution (a rule, not a measurement):** `sebastian/clients/google/drive/client/
_deterministic.py` defines one candidate: the object with the earliest `createdTime`
wins; ties, including objects with no `createdTime`, are broken by the
lexicographically smallest `id`. `pick_oldest` applies it to file lookups, folder-path
lookups, and the folder reused by `upload_file`, so the lookup and the upload land on
the same duplicate.

**What would prove the rule against Drive:**
`tests/integration_tests/mietplan/test_upsert.py::
test_a_duplicated_name_is_answered_deterministically_live` uploads the same path twice
and asserts repeated lookups return the same (oldest) id. Unit tests pin the rule
itself with a fake service. The rule is still a choice this repository imposes; it is
not a measured property of Google Drive.

**Deliberate deviation from the literal wording of D17/#126:** "the existing upload
path and its other caller are unchanged" is now contradicted in one narrow respect —
`find_or_create_folder` uses the same `pick_oldest` candidate as `find_file`. Without
a shared rule the lookup and the upload can land on different duplicates, which
breaks the upsert. Upload metadata, `upload_file`'s signature and the `winsim` call
site are otherwise unchanged.

## V5 — walk cost and the Functions timeout (estimated, recorded)

**Assumed/estimated:** a whole-webdepot (`maxFileAge=all`) resync costs about `2F`
portal requests for the walk plus one download, one Drive lookup and one
create/update per file (`F` folders, `N` files). That plausibly exceeds the
Consumption-plan 5-minute default and the 230-second HTTP response cap; the
deployment plan type is not recorded in the repo.

The finding, the request-count estimate and the mitigations (use `folder` scope;
the timer keeps its one-day window; runs are safe to repeat; `host.json` unchanged)
are recorded in `docs/specs/mietplan-v5-timeout.md`. **Recorded, not measured.**

**What would prove it:** a live whole-webdepot resync against the deployed function,
reading the returned `durationSeconds` and comparing it with the actual
`functionTimeout` / HTTP cap, plus the wall time of
`tests/integration_tests/mietplan/test_search_live.py` (which already performs one
full walk per session). No Azure or deployment access was available here.
