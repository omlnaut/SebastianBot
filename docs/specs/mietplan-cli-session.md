# Session export — `seadepot`, an agent-facing Mietplan (webdepot) CLI, and a manual resync

- **Date:** 2026-12-06
- **Kind:** grilling session. **Spec only — no code written.** Implementation happens in the devcontainer by agents, from tickets cut out of this export.
- **Repo:** `omlnaut/SebastianBot` (Python 3.12, Azure Functions, "pragmatic clean architecture").
- **Origin of the need:** the vault agent can read the filesystem, gdrive and mail (via `seamail`), but not the rental documents in the Mietplan webdepot. It needs to *find* the right document online without a human clicking through the portal. Separately, the nightly Mietplan → Google Drive sync occasionally fails, and files that fell outside the one-day age window are never retried, so there is no way to repair a missed day.
- **Relationship to `docs/specs/gmail-cli-session.md`:** same shape, same runtime model (host process, `uv` venv, PATH shim, env-var credentials, JSON only, no `cloud/` import), deliberately independent install.

---

## 1. What already exists (recon done in this session)

Read, not guessed. Paths are repo-relative.

| Path | What it gives us |
| --- | --- |
| `sebastian/clients/mietplan/client/client.py` | `MietplanClient(credentials)`: `walk_from_top_folder()` (generator of `MietplanFolder`), `download_file(download_path) -> bytes`. Logs in in the constructor. |
| `sebastian/clients/mietplan/client/_login.py` | `login(session, username, password)`: fetches a CSRF token from `https://mietplan-dresden.de/login/`, posts it with the credentials. **Never verifies the result.** |
| `sebastian/clients/mietplan/client/_walk_from_top_folder.py` | The portal's JSON endpoints — `msg=getFolders&fdFolder=<id>` and `msg=getFiles&fdFolder=<id>` — visited depth-first from `_MAIN_FOLDER_ID = "ac4do35ktgfi79j8ids35om8udm"`. **Raises on the first failing folder**, killing the whole walk. There is **no server-side search endpoint**; a file is only discoverable by walking to its folder. |
| `sebastian/clients/mietplan/client/_download_file.py` | `download_file_to_ram(session, download_path)`: `https://mietplan-dresden.de` + `filepath`, bytes in RAM. |
| `sebastian/clients/mietplan/client/_models.py` | Raw folder/file models (`name`/`folder_id`/`has_subfolders`; `creation_date`/`download_path`/`filename`). |
| `sebastian/clients/shared/retry_session.py` | `create_retry_session()`: tenacity/urllib3 retries on connect/read/`429,500,502,503,504`, browser User-Agent. Used for both login and data requests. |
| `sebastian/domain/mietplan.py` | `MietplanFile{creation_date, name, url}`, `MietplanFolder{id, path: list[str], files}`. |
| `sebastian/usecases/features/mietplan/handler.py` | The usecase: walk, keep files with `creation_date` inside `max_file_age`, download each, upload to Google Drive folder `19gdVV_DMtdQU0xi7TgfKJCRRc4c7m0fd` at `folder/path/name`, then return one `SendMessage` listing the uploaded paths. |
| `sebastian/usecases/features/mietplan/protocols.py` | `IMietplanClient` (`walk_from_top_folder`, `download_file`), `IGoogleDriveClient` (`upload_file`). |
| `sebastian/clients/google/drive/client/client.py` + `upload_file.py` | `GoogleDriveClient.upload_file(UploadFileRequest)`: ensures the folder chain (`find_or_create_folder`/`ensure_folder_path`) and then **always** `files().create(...)` — same name, no existence check. **The only method on the client.** |
| `cloud/functions/features/mietplan_function.py` | Timer (daily 21:01) **and** an existing HTTP route `check_mietplan`, both calling `perform_usecase_from_request(mietplan.Request(max_file_age=timedelta(days=1)), resolve_mietplan)` — the window is hardcoded. |
| `function_app.py` | `func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)` → the HTTP route needs `?code=<function key>`. |
| `cloud/helper/secrets.py`, `cloud/dependencies/clients.py` | `MietplanCredentials` (`username`/`password`) from Key Vault via `DefaultAzureCredential`; `resolve_mietplan_client()` is `lru_cache`d. |
| `cli/mail.py`, `scripts/setup_seamail.sh`, `cli-requirements.txt`, `tests/unit_tests/cli/test_mail_cli.py`, `tests/unit_tests/test_cli_requirements.py` | The seamail precedent reused here: argparse parser → `run(argv, service)` for tests, `main()` for the real process; JSON envelope; `kind` on stderr; direct-dependency file with drift guard. |

### 1.1 Defects that bite this work specifically

1. **No idempotency.** `upload_file` always creates a new file, so any re-run of the sync duplicates every file still inside the age window. The nightly run already duplicates within its window; a "resync" would multiply it.
2. **No repair path.** A failed night loses its files permanently, because tomorrow their `filecrea` is outside `max_file_age`.
3. **A mid-walk failure kills the whole walk.** One timed-out folder yields zero results, which is indistinguishable from "nothing there".
4. **Login is unverified.** A rejected password produces an empty walk, so a client can report "no files" with confidence it has not earned.
5. **No searchability.** Navigation-only endpoints mean "find the 2024 Nebenkostenabrechnung" is a full walk for every question.

---

## 2. The grilling session (round by round)

Recommendations carried no "rejected" note were accepted. Answers are quoted verbatim.

### Round 1 — roots

**Q1 — What the CLI is for.** Read tool (`search` + `download`) or also the write/sync side?
➡️ Read tool, mirroring seamail's read path; sync stays out of this binary because it needs GDrive + Key Vault. → **"q1 agree, gdrive sync is done by another agent"**

**Q2 — Where "resync all" lives.** The existing Azure HTTP route already triggers a sync; it is merely hardcoded to one day.
➡️ A parameter on that route, not a CLI verb. → **"q2 agree"**

**Q3 — Duplicate safety of a resync.** Should resync skip files that already exist on Drive?
➡️ Idempotent: skip and report `skipped`. → **"q3 yes"** — *superseded in round 3; corrections must win.*

**Q4 — Credentials & runtime.** `SEAMIETPLAN_CREDENTIALS` env var holding `{"username":…,"password":…}` JSON, own loader, no `cloud/` import, no Key Vault.
➡️ Yes. → **"q4 yes"**

**Q5 — Name and install.** `cli/mietplan.py` called `seadepot`, own idempotent setup script, reuse `cli-requirements.txt`, extend the drift guard.
➡️ Yes. → **"q5 yes"**

**Q6 — Regression guard.** The client and usecase have **no tests at all**; write characterization tests first?
➡️ Yes, tests before touching the resync path. → **"q6 yes"**

### Round 2 — the read path

**Q1 — Search filters.** No query language exists, so walk + local filter: positional substring, `--folder`, `--after`, `--before`, `--limit` (default 50, cap 500), no fuzzy matching.
➡️ Yes. → **"q1 yes"**

**Q2 — Result shape and download addressing.** Hits carry `{path, folderId, name, creationDate, url}`; `download <path>` re-walks to resolve the url; no `--url` escape hatch.
➡️ Yes. → **"q2 yes"**

**Q3 — Partial walk.** Opt-in tolerant mode (partial results + `warnings`, exit 0), usecase stays strict.
➡️ Yes. → **"q3 yes"**

**Q4 — Login verification.** Probe after login; a rejection becomes `kind: auth`, not an empty result.
➡️ Yes. → **"q4 yes"**

**Q5 — Resync route contract.** `?maxFileAge=all|<days>`, `max_file_age: timedelta | None`, timer keeps 1 day, no Telegram on manual runs.
➡️ Yes. → **"q5 yes"**

**Q6 — Conflict policy on an existing Drive path.** skip / overwrite / disambiguate / archive.
➡️ → **"q6 neither, keep both copies"** — *contradicted round 1's skip; taken up in round 3.*

### Round 3 — resolving the contradiction

**Q1 — What "keep both copies" protects.** "Never lose a Drive file" (always upload, duplicates) vs "idempotency wins" (skip) vs "disambiguate names" vs "archive the old copy".
➡️ Recommend the literal reading (always upload) but name its cost; offer `c` if the real concern is a corrected PDF silently replacing the old one.
→ **"nvm, just replace it then. i'd want the latest version since there might be corrections in there"**

### Round 4 — what "replace" forces

**Q1 — Replace mechanics.** Update the existing file in place (stable id, parents, sharing) rather than delete-then-create.
➡️ Yes. → **"q1 yes"**

**Q2 — "Nothing to do" detection.** Always re-upload vs marker in Drive `appProperties` vs marker + `full=true` escape hatch.
➡️ **c**: marker plus a force flag, with "does the portal bump `filecrea` on a corrected upload?" as a verification item. → **"q2 c"** — *superseded in round 6: the marker rested on a question that cannot be answered, so the skip logic was dropped entirely.*

**Q3 — One rule everywhere.** The replace-instead-of-duplicate rule also applies to the timer path.
➡️ Yes. → **"q3 agree"**

**Q4 — Deletions.** Add + update only, never delete Drive files (a partial walk must not look like deletions).
➡️ Yes. → **"q4 agree"**

**Q5 — Route scope + dry run.** `maxFileAge`, `folder`, `dryRun`, plus `full`; JSON response; no Telegram on any HTTP-triggered run.
➡️ Yes. → **"q5 yes"** — *`full` removed in round 6 with the marker.*

**Q6 — Reporting/regression shape.** Characterization tests against today's behaviour first, then flip the duplicate test to "replace"; everything else stays locked.
➡️ Yes. → **"q6 yes"**

### Round 5 — remainder

**Q1 — Where the Drive capability lives.** Additive methods on the shared `GoogleDriveClient` (`find_file`, `replace_file`, optional `app_properties`), protocol extended for mietplan only, `winsim` untouched.
➡️ Yes. → **"q1 agree"**

**Q2 — What `download` writes.** Mirror the folder path under `--out`, sanitize each segment, usage error rather than escaping `--out`.
➡️ Yes. → **"q2 agree"**

**Q3 — Search returns files only.** Empty folders are invisible; `scannedFolders` reports the walk's extent.
➡️ Acceptable. → **"q3 agreee"**

**Q4 — Integration tests.** New `tests/integration_tests/mietplan/` (Key Vault, dev machine only) as the only place the replace logic meets reality.
➡️ Yes. → **"q4 yes"**

**Q5 — Artifact.** This spec plus 4 tickets via `gh`, nothing implemented before the cut is approved.
➡️ Yes. → **"q5 yes"**

### Round 6 — the marker had to go

**Q1 — V1 is unanswerable** (the portal's uploads are not ours to control), so the `appProperties` marker rests on an assumption nobody can check: if `filecrea` does not change on a corrected upload, a resync would skip exactly the file that needed replacing. Drop the marker and always download + replace inside the scope, with no `skipped` and no `full` flag?
➡️ Yes — one rule, no stored state, no unverifiable assumption; the nightly run costs what it costs today (it already downloads its whole window), while a manual whole-webdepot resync becomes expensive and stays rare.
→ **"can't check v1 because i dont own the upload. find a solution that just works. doesnt matter if we don't catch edge cases here, this rarely happens"** → **"yes"**

---

## 3. Settled decisions

- **D1 — Purpose.** `seadepot` is a read tool for an agent: find files in the Mietplan webdepot, print them as JSON, and write one file to disk on request. The Google Drive sync is **not** part of this binary.
- **D2 — Runtime.** Plain host process, no container, no Azure login, no Key Vault, no import of `cloud/` — identical to seamail. WSL today, Raspberry Pi later.
- **D3 — Install.** `cli/mietplan.py`, binary `seadepot`, own idempotent `scripts/setup_seadepot.sh` creating `~/.local/share/seadepot/venv` and a shim on `PATH`, dependencies from the existing `cli-requirements.txt` (mietplan needs only `requests`, `beautifulsoup4`, `pydantic`, which are already declared). `tests/unit_tests/test_cli_requirements.py` is extended to cover both entry points. `pyproject.toml`, `requirements.txt` and the Azure deployment are untouched.
- **D4 — Credentials.** `SEAMIETPLAN_CREDENTIALS` holds the `{"username":…,"password":…}` **JSON content**. A loader next to `sebastian/clients/mietplan/credentials.py` raises `CredentialsError` (missing/invalid) → `kind: auth` on stderr, exit 1, never a traceback. The bot keeps Key Vault; the CLI never writes credentials anywhere.
- **D5 — Output.** JSON only, one object per invocation on stdout; errors are JSON on stderr with `kind` ∈ `auth|api|usage|io`; exit codes `0` ok, `1` runtime, `2` usage. No table/plain renderers.
- **D6 — Search.** Full tree walk + local filters. Optional positional case-insensitive substring matched against `folder/path/name`; `--folder <prefix>`; `--after`/`--before` on `filecrea`; `--limit` default 50, hard cap 500. No fuzzy matching, no ranking, no cache.
- **D7 — Search output.** Envelope `{command, filters, count, scannedFolders, truncated, files, warnings}`; each file `{path, folderId, name, creationDate, url}`. Files only — empty folders never appear.
- **D8 — Download.** `seadepot download <path> --out DIR [--force]`, where `path` is exactly what `search` echoed. Resolution re-walks the tree. The output mirrors the folder path under `DIR`, creating parents; each segment is sanitized; a path that cannot be made safe is a usage error rather than a write outside `DIR`; existing files are only replaced with `--force`.
- **D9 — Tolerant walk.** The walk gains an opt-in tolerant mode: partial results plus `warnings` (`{folderId, path, error}`), exit 0. The usecase keeps the strict raise-on-first-error behaviour.
- **D10 — Auth is verified.** After login the client probes the root folder; a non-JSON/login-page response raises `MietplanAuthError`. The CLI maps it to `kind: auth`. Silent empty results are forbidden.
- **D11 — Resync home.** The existing function-auth HTTP route `check_mietplan` gains `maxFileAge=all|<days>`, `folder=<path-prefix>` and `dryRun=true`. `mietplan.Request.max_file_age` becomes `timedelta | None` (`None` = whole webdepot). The timer keeps one day. No Telegram message on any HTTP-triggered run; the summary is the JSON response.
- **D12 — Upsert, never duplicate.** A file whose full path already exists in the target Drive folder is **replaced in place** (`files().update`, file id, parents and sharing preserved) with the freshly downloaded content. Latest portal version wins, because a re-issued PDF may contain corrections.
- **D13 — Never delete.** Resync adds and updates only. Files present in Drive and absent from the webdepot stay.
- **D14 — Always replace in scope.** No marker, no `skipped`, no `full` flag: every file inside the scope is downloaded and uploaded or replaced on every run, so afterwards each Drive copy is byte-identical to the portal. Correctness by construction, no stored state to rot, no assumption about whether the portal bumps `filecrea` on a corrected upload (that question cannot be answered — the uploads are not ours). Accepted cost: a whole-webdepot resync is N downloads + N uploads, run manually and rarely; the nightly window is unaffected because it already downloads every file it syncs. A content-hash cache was rejected — it still pays the download, which is the expensive half.
- **D15 — One rule everywhere.** The timer path and the manual resync share the same upsert behaviour; only the age window, folder scope and dry-run differ.
- **D16 — Resync response.** `{dryRun, maxFileAge, folder, scannedFolders, uploaded[], replaced[], failed[], durationSeconds}`. `uploaded` = paths that did not exist in Drive, `replaced` = paths whose existing file was updated — both derived from the path lookup, not from a marker.
- **D17 — Drive surface.** Additive `GoogleDriveClient.find_file(filename_with_path, base_folder_id)`, `replace_file(file_id, content, mime_type)`, and an optional `app_properties` field on `UploadFileRequest`; `upload_file` and the `winsim` call site are unchanged; `mietplan.IGoogleDriveClient` names only what mietplan needs.
- **D18 — Tests.** Characterization tests for the usecase (age filter, upload path building, Telegram message text) and for the client walk/filter land **first**, against today's behaviour; the duplicate test then flips to "replace". CLI unit tests mirror `tests/unit_tests/cli/test_mail_cli.py` (injected fake service, no network). New `tests/integration_tests/mietplan/` covers walk, download and find-after-upload against the live portal (Key Vault, dev machine only, not CI).
- **D19 — Artifact.** This export and four tickets; no implementation until the cut is approved.

---

## 4. Derived contract

### 4.1 CLI surface

```
seadepot search [SUBSTRING] [--folder PREFIX] [--after YYYY-MM-DD] [--before YYYY-MM-DD]
                [--limit N]
seadepot download <folder-path>/<filename> --out DIR [--force]
```

```jsonc
// search
{ "command": "search",
  "filters": {"substring": "nebenkosten", "folder": null,
              "after": "2024-01-01", "before": null, "limit": 50},
  "count": 3, "scannedFolders": 42, "truncated": false,
  "files": [ { "path": "Nebenkostenabrechnung/2024.pdf",
               "folderId": "…", "name": "2024.pdf",
               "creationDate": "2024-05-01", "url": "/auctores/…/file.pdf" } ],
  "warnings": [ {"folderId": "…", "path": "Archiv/2019", "error": "read timeout"} ] }

// download
{ "command": "download", "path": "Nebenkostenabrechnung/2024.pdf",
  "file": {"path": "/home/pi/Downloads/Nebenkostenabrechnung/2024.pdf", "bytes": 91234} }

// error
{ "command": "download", "error": {"kind": "usage", "message": "…"} }
```

- `--limit` truncates the **result list**, not the walk (the walk must run to know what matched); `truncated: true` says so.
- `warnings` is always present (empty when the walk was clean); a warning does not change the exit code.
- No `--url`, no `--json`, no `--format`: one shape, always.

### 4.2 Resync route

```
POST /api/check_mietplan?code=<key>
     [&maxFileAge=all|N] [&folder=<path-prefix>] [&dryRun=true]
```

```jsonc
{ "dryRun": false, "maxFileAge": "all", "folder": null,
  "scannedFolders": 42, "durationSeconds": 63.4,
  "uploaded": ["Nebenkostenabrechnung/2024.pdf"],
  "replaced": ["Mietvertrag/mietvertrag.pdf"],
  "failed":   [{"path": "Archiv/2019/x.pdf", "error": "…"}] }
```

- `failed` entries do not abort the run; the response is the repair report.
- Timer invocation is unchanged: one day, Telegram summary as today, now with duplicates replaced instead of created.
- Every run in scope downloads and writes every file, so a second run reports the same files under `replaced` (or `uploaded`) again. That is the intended behaviour, not an inefficiency to optimise away.

---

## 5. Verification items the implementer must settle by running code

- [ ] **V1** — What does an expired/rejected session return from `getFolders` — JSON, an HTML login page, or a redirect? D10's probe must key off the real signal.
- [ ] **V2** — What do real `filepath` values look like (umlauts, spaces, `&`, query params) and does `html.unescape` + URL-join reproduce the exact bytes the portal serves?
- [ ] **V3** — Does `files().update(... media_body=...)` keep the file id, parents and sharing, and does it complete for a file of realistic invoice size?
- [ ] **V4** — Are Drive folder lookups by path unambiguous when a folder name already exists twice under the same parent (created by the old duplicate bug)? "Replace" needs a deterministic target.
- [ ] **V5** — Walk cost on the real tree: how many folders, how many requests, how long a `search` with no filter takes. If it is minutes, `--limit` semantics (truncate output, not the walk) must be visible in the docs the agent reads, and a whole-webdepot resync must be checked against the Functions timeout.

---

## 6. Out of scope

- Any Google Drive work inside `seadepot`, and any Key Vault access from it.
- Deleting or trashing Drive files, folders or duplicates created by the old bug (a cleanup, if wanted, is a separate one-off).
- Server-side search, local index, cache or embeddings; fuzzy/semantic matching; ranking.
- Human-facing output (tables, colour), and any `--format` switch.
- Uploading, moving or renaming anything in the webdepot; the portal is read-only from our side.
- Migrating `winsim` or other consumers onto the new Drive methods.
- An MCP wrapper or pi custom tool — the CLI is the portable interface.

## 7. Consequences worth remembering

- The nightly sync changes behaviour on purpose: same-path files are now replaced rather than duplicated, so the old duplicate bug stops growing. Anything that depended on duplicates being created is gone.
- `max_file_age: timedelta | None` widens a model the timer relies on; `None` must mean "everything", never "nothing" — a test should pin that.
- A resync of the whole webdepot downloads and uploads **every** file, every run. On a slow portal that is a long function invocation (see V5) and the Functions timeout is a real constraint. The absence of a skip check is deliberate: it must not be "optimised" back into a stored marker whose correctness nobody can verify.
- Two CLIs, one precedent: `seamail` and `seadepot` share conventions but neither install nor code path. Duplicating the envelope/error helpers is accepted rather than extracting a framework for two callers.
