# Session export — `seamail`, an agent-facing Gmail search CLI

- **Date:** 2026-10-19
- **Kind:** grilling session. **Spec only — no code written.** Implementation happens in /workspaces/SebastianBot by a dev-environment agent, from tickets split out of this export.
- **Repos:** `omlnaut/SebastianBot` (this repo, Python 3.12, Azure Functions, "pragmatic clean architecture"), `omlnaut/SebastianSkills` (the agent's skills repo, where the session ran).
- **Branch:** `gmailCLI` in this repo. This file is the raw material for the ticket split; the ticket-cutting skill owns how it is sliced.
- **Relocation note:** first committed to SebastianSkills (`docs/specs/`), which was an oversight — it belongs here. Body below is unchanged; only this header is new. Round-2 Q7's quoted answer still says "sebastianSkills (gmailCLI)"; the quote is left verbatim, this repo/`gmailCLI` is where the artifact actually lives.
- **Origin of the need:** the vault agent can search the filesystem, gdrive and Home Assistant, but not mail. `Inbox/Project planner-handler.md` in the vault wants "ingest new information automatically from email"; the concrete daily job is answering *"which mails are about X"* (e.g. "what did the installer say about the KfW-Förderung") and then reading the one that matters.

---

## 1. What already exists in SebastianBot (recon done in this session)

Read, not guessed. Paths are repo-relative.

| Path | What it gives us |
| --- | --- |
| `sebastian/clients/google/gmail/client/client.py` | `GmailClient(credentials)`: `fetch_mails(query)`, `download_pdf_attachments(mail)`, `modify_labels(...)`, `get_labels()` |
| `sebastian/clients/google/gmail/client/service_wrapper.py` | `GmailServiceWrapper`: `build("gmail","v1")`, `fetch_message_ids`, `fetch_full_mail`, `download_pdf_attachment`, `modify_labels`, `fetch_labels`, plus `to_full_mail_response()` (the payload parser) |
| `sebastian/clients/google/gmail/client/modify_labels.py`, `download_pdf_attachments.py` | thin helpers over the wrapper |
| `sebastian/clients/google/gmail/client/retry_decorator.py` | `retry_on_network_error` — tenacity, retries SSL/socket/`ConnectionError`/OSError and HTTP 5xx, not 4xx |
| `sebastian/domain/gmail.py` | `FullMailResponse` (pydantic, with `has_label()` and `age()`), `GmailLabel` (dataclass `name`+`label_id`), `GmailLabels` (hardcoded enum: `ToRead`, `Unread`, `Processed`), `GmailLabelResponse`, `PdfAttachment`, `PdfMessagePart` |
| `sebastian/usecases/shared/query_builder.py` | `GmailQueryBuilder` — fluent builder (`from_email`, `subject`, `has_label`, `is_unread`, `has_attachment`, `after/before/on_date`, `exclude_me`, `build`) |
| `cloud/dependencies/clients.py` | `resolve_gmail_client()`, `load_google_credentials()` — both `lru_cache`d, credentials via Key Vault |
| `cloud/helper/secrets.py` | `SecretKeys.GoogleCredentials` → `GoogleSecret{credentials: Credentials}` from `https://omlnaut-sebastian.vault.azure.net/` via `DefaultAzureCredential` |
| `investigations/google_token/create_credentials.py` | the OAuth app + scopes: `gmail.modify`, `tasks`, `drive`, `calendar`; writes `{"credentials": <authorized_user json>}` |
| `tests/integration_tests/gmail/` | `conftest.py` fixture `gmail_client` (via `resolve_gmail_client`), `test_fetch_mails.py`, `test_labels.py`, `test_pdf_attachments.py` |

Existing consumers of `fetch_mails`: `usecases/features/mail_check`, `delivery_ready`, `return_tracker`, `winsim` (through per-feature `protocols.GmailClient`). **None of them may change behaviour in this project.**

### 1.1 Defects that bite a *search* tool specifically

1. **No `format=metadata` path.** `fetch_mails` = one `messages.list` + one **full** `messages.get` per hit — N+1 requests and full body bytes for every hit.
2. **No pagination.** `messages.list` is called with no `maxResults` and no `pageToken` (`service_wrapper.py:fetch_message_ids`), so results are silently capped at Gmail's default page (100) and there is no way to get the rest.
3. **No control over request depth or headers.** No `metadataHeaders`, no `fields`.
4. **`text/plain`-only mail body is dropped.** `_extract_email_body` returns the first top-level `text/html` part; if a message has only `text/plain` (or the HTML is nested deeper), `content == ""`.
5. **Nested attachments are invisible.** `_extract_pdf_parts` scans only `payload["parts"]`, so `multipart/mixed → multipart/alternative` + PDF layouts lose the PDF.
6. **Only two headers are parsed** (`Subject`, `From`); no `To`, `Cc`, `Date`, `Message-Id`. `internalDate` (epoch ms string) is the only date.
7. **`GmailQueryBuilder` is a small subset** of Gmail's operators (no `to:`, `cc:`, free text, `newer_than`, `larger:`, negation, grouping) — moot for this project, see D2.

---

## 2. Environment facts established this session (WSL host)

- `python3` = 3.12.3, but **no `pip`, no `pipx`, no `uv`**, and `python3 -m venv` **fails** (ensurepip missing). Nothing Python-installable without `sudo apt` or a bootstrap installer.
- **Docker is not usable from this WSL**: `docker` CLI exists, `/var/run/docker.sock` is absent, `docker -c desktop-linux version` errors.
- `node`/`npm` are present (nvm).
- `az` is absent → the bot's Key Vault path (`DefaultAzureCredential`) is not available to the agent here.
- SebastianBot is `package-mode = false` in `pyproject.toml` → **not pip/pipx-installable** as it stands.
- pi (the vault agent) runs in WSL today; planned move to a Raspberry Pi later. The CLI must survive that move.

---

## 3. The grilling session (round by round)

Answers are quoted verbatim. All recommendations below that carry no "rejected" note were accepted.

### Round 1

**Q1 — Primary use case.** "Given a vague question about my life, find the 1–5 emails that matter, then read one in full and maybe pull an attachment", or "bulk/mailbox housekeeping"?
➡️ Recall tool first. → **"agree"**

**Q2 — Runtime home & invocation.** Code in SebastianBot but callable from the agent's session.
➡️ Code stays in SebastianBot, installable as a host-level command. → **"agree"**, plus: *"pi runs in wsl currently. later planned to move to a rasperry pi, but would run on the host too. im a fan of docker for such scenarios... but is that overkill?"*

**Q3 — Command surface.** `search`, `show`, `thread`, `labels`, `attachments`, `mark`, `label`.
➡️ v1 = read path only (`search`, `show`, `labels`, `attachments`); write verbs later under a different safety argument. → **"agree"**

**Q4 — What `search` returns per hit.** Metadata only, or full bodies?
➡️ Metadata only; body comes from `show`. 50 metadata hits ≈ 1 full mail. → **"agree"**

**Q5 — Filter dialect.** Structured flags + raw-query escape hatch?
➡️ Both, echo the effective query. → *"cli will only ever be used by agent, who probably knows the raw gmail query anyway. so no need for flags at all, just pass in the raw gmail query string, right?"* — **accepted: raw query only, no filter flags.**

**Q6 — Output contract.** JSON envelope vs NDJSON; `--format json|table|plain`.
➡️ JSON envelope default, NDJSON for streaming, table for the human. → *"no need 'for me', the cli is only for the agent"* — **accepted: JSON only, no human format.**

**Q7 — Write operations and blast radius.** Single-id vs batch-by-query, dry-run default.
➡️ Single-id, dry-run unless `--apply`, no "label everything matching this query". → *"write not in scope"* — **accepted: no Gmail writes at all.**

**Q8 — Where the spec lands.** Vault project vs repo ticket.
➡️ Vault project for *why* + one implementation ticket in the repo for *what*. → *"agree, but instead of a single 'ticket' file make it an export of this session. i'll use a dedicated 'ticket' skill to split that into tickets. put that onto its own branch and push in sebastianSkills (gmailCLI)"*

### Round 2

**Q1 — Is docker overkill?** Facts above: no daemon, no socket.
➡️ Yes. One short-lived process reading a token and calling one HTTP API; container adds a daemon dependency, a token-mounting problem and a rebuild per code change. → **"agree"** (revisit at the Pi move).

**Q2 — How the command gets installed.** apt+pipx / uv / rewrite in Node.
➡️ `uv` (sudo-free, one static binary, bootstraps its own Python, portable to the Pi); `setup.sh` gains one idempotent step. → **"agree"**

**Q3 — Packaging / entry point.** Flip `package-mode` / dedicated venv + shim / `uv run --with-requirements` per call.
➡️ Dedicated venv at `~/.local/share/seamail/`, shim on `PATH`, `PYTHONPATH=<repo>`, `python -m …`; no change to the deployable packaging. → **"b, but dependencies probably not from requirements.txt. that one is auto-generated from the poetry toml file and contains ALL dependencies (transitive)."** — **accepted: direct deps only, see D8.**

**Q4 — Credentials source.** Local token JSON / az+Key Vault per run / env var.
➡️ Local token JSON, mode 600, env-var override; CLI must not import `cloud/`. → *"a, i'll just put the token into a json and have something export that as env var automatically"* — **accepted: env var carrying the JSON content, see D9.**

**Q5 — Client gaps: fix now or isolate the CLI.** Own parsing vs one shared parser with the bot migrating later.
➡️ One shared payload parser, fixed once; new additive client methods; bot migration out of scope. → **"agree"**

**Q6 — Final verb set + binary name.** `attachments` and `thread` in v1? Name?
➡️ `attachments` **in** (read-only, and it is the path that gets an invoice PDF out of mail and into gdrive); `thread` **out**; name `seamail`. → **"agree"**

**Q7 — Export artifact.** Full session export into SebastianSkills on branch `gmailCLI` at `docs/specs/gmail-cli-session.md`, only that file committed (the two dirty `recipes/zigbee-topology/` files stay untouched on `main`), verbatim transcript plus highlighted decisions.
➡️ As stated. → **"agree"**

### Round 3

**Q1 — Dependency provisioning** (`requirements.txt` is all-transitive; the repo has no `[project]`, so uv sees no deps).
➡️ Committed `cli-requirements.txt` with only the direct deps, comment naming `pyproject.toml` as source of truth. → **"a"**

**Q2 — Credentials shape.**
➡️ `SEAMAIL_GOOGLE_CREDENTIALS` holds the JSON **content** (not a path), loader accepts `{"credentials": {…}}` and the bare credentials object. → **"a"**

**Q3 — Where the code sits.** Top-level `cli/` (peer of `cloud/`) vs `sebastian/cli/` vs a usecase.
➡️ Top-level `cli/`, adapter over the client layer, no usecase, `sebastian/` stays free of entrypoint concerns. → **"yes"**

---

## 4. Settled decisions

- **D1 — Purpose.** A *recall* tool: find the few relevant mails cheaply, then read one in full, then optionally pull an attachment. Bulk processing stays with the existing bot usecases.
- **D2 — Query dialect.** The CLI takes **Gmail's own query string, verbatim**. No filter flags, no query DSL of our own, no changes to `GmailQueryBuilder`. The agent is expected to know `from:`, `subject:`, `after:`, `has:attachment`, `-label:`, `is:unread`, `in:anywhere`, `rfc822msgid:`, `OR`, parentheses. Non-filter options (depth, limit, paging, output) are ordinary flags.
- **D3 — Read-only.** No `mark`, no `label`, no sending, no deletion, no archiving. Gmail-side writes are out of scope for the whole project.
- **D4 — Depth.** `search` returns **metadata only**; `show <id>` is the only path to a body.
- **D5 — Output.** JSON only, one object per invocation, agent-first. No table/plain renderers.
- **D6 — Verb set (v1).** `search`, `show`, `labels`, `attachments`. No `thread`.
- **D7 — Runtime.** Plain Python process on the host (WSL, later Raspberry Pi). **No docker.**
- **D8 — Install.** `uv` provisions one dedicated venv at `~/.local/share/seamail/venv` from a new committed **`cli-requirements.txt`** (direct deps only: `google-api-python-client`, `google-auth`, `google-auth-oauthlib`, `pydantic`, `tenacity`, `beautifulsoup4`; header comment: *derived from `pyproject.toml`, keep in sync*). A shim at `~/.local/bin/seamail` runs that venv's python with `PYTHONPATH` pointing at the repo, `python -m cli.mail "$@"`. `setup.sh` gains one idempotent step (install uv if missing, create/refresh the venv, write the shim). **`pyproject.toml` is not modified** — `package-mode = false` stays, Azure deployment is untouched.
- **D9 — Credentials.** Env var **`SEAMAIL_GOOGLE_CREDENTIALS` containing the JSON content**. Loader accepts both `{"credentials": {…}}` (the `investigations/google_token` / Key Vault secret shape) and a bare authorized-user object. Missing/invalid → JSON error on stderr naming the variable; never a traceback. Refresh happens in-process from the stored refresh token; **no write-back to any store**. The CLI **must not import `cloud/`** (no azure deps at runtime).
- **D10 — Layering.** New top-level package `cli/` (peer of `cloud/`), a thin adapter over `sebastian/clients/google/gmail`. The structured parts (payload parsing, hit normalization, body rendering) live in `sebastian/` so the bot can adopt them later; the `cli/` layer only does argv → request → JSON.
- **D11 — Shared parser.** One payload-parsing module (in `sebastian/clients/google/gmail/…`) that fixes D-facts 4, 5, 6 from §1.1: `text/plain` preferred with HTML fallback, recursive part traversal for attachments, full header set. New additive client methods; `fetch_mails` and its consumers are **not** migrated in this project.
- **D12 — Credential model unchanged for the bot.** Key Vault + `DefaultAzureCredential` stays the bot's path; the CLI gets its own small loader. Two loaders, one `Credentials` type.
- **D13 — Artifact.** This export. Tickets are cut from it by the ticket skill; implementation in the devcontainer.

---

## 5. Derived contract (what a ticket should be able to pin down)

Only what the decisions imply — nothing here overrides §4.

### 5.1 Surface

```
seamail search "<gmail query>" [--limit N] [--page-token TOKEN]
seamail show <message-id> [--format text|html] [--max-chars N]
seamail labels
seamail attachments <message-id> --out <dir> [--force]
```

- `search`: `messages.list(q=…, maxResults=limit, pageToken=…)`; **default limit 25, hard cap 200**; **never auto-paginate** — return `nextPageToken` and let the agent ask.
- `show`: `messages.get(format="full")`, normalized; `--format text` (default) = `text/plain` part, or HTML converted via the existing `beautifulsoup4` dep; `--format html` = raw HTML part; `--max-chars` default 20000 with an explicit `truncated` flag in the response.
- `labels`: `users().labels().list()` — id, name, type, visibility. Also used internally by `search`/`show` to resolve label ids → names.
- `attachments`: `users().messages().attachments().get()` per attachment of that message, written into `--out` with sanitized filenames; refuse to overwrite without `--force`; print the written paths and sizes. Attachment ids are short-lived — fetch them in the same run as the message.
- Exit codes: `0` ok, `1` runtime/API error, `2` usage error. Errors are JSON on **stderr**, nothing but JSON on stdout.

### 5.2 JSON shapes (sketch — the implementer may refine field names, not the envelope)

```jsonc
// search
{ "command": "search", "query": "<effective query>", "limit": 25,
  "count": 12, "resultSizeEstimate": 12, "nextPageToken": "…" | null,
  "hits": [ { "id": "…", "threadId": "…", "from": "…", "to": ["…"],
              "cc": [], "subject": "…", "date": "2026-10-14T09:12:03+00:00",
              "internalDate": "1760430723000", "labels": ["Inbox","Klima"],
              "labelIds": ["…"], "snippet": "…", "sizeEstimate": 48213,
              "hasAttachments": true,
              "attachments": [{"filename":"Rechnung.pdf","mimeType":"application/pdf","size":91234}] } ] }

// show      → { "command":"show", "message": { …hit fields…, "body": "…", "bodyFormat":"text", "truncated": false } }
// labels    → { "command":"labels", "labels": [{"id":"…","name":"…","type":"user"}] }
// attachments → { "command":"attachments", "messageId":"…", "files":[{"path":"…","size":91234}] }
// error     → { "command":"…", "error": {"kind":"auth|api|usage|io", "message":"…"} }
```

`search` requests `format=metadata` with `metadataHeaders=From,To,Cc,Subject,Date`; attachment names come out of the metadata payload's part tree (see V1). Labels are resolved to names per invocation (one `labels.list`, cheap).

---

## 6. Verification items the implementer must settle by running code

Not answered by reading; do not assume.

- [ ] V1 — Does `format=metadata` include the **nested** part tree with `filename`/`mimeType`/`size` (needed for `hasAttachments` without a second call)?
- [ ] V2 — Is `snippet` present in a `format=metadata` response, and is `resultSizeEstimate` worth surfacing?
- [ ] V3 — Real-world bodies: which mails are `text/plain`-only, which are HTML-only, which nest the body inside `multipart/related`? Confirm the fallback order against actual mail, not fixtures.
- [ ] V4 — Are the `gmail.modify` scopes in `investigations/google_token/create_credentials.py` sufficient for `messages.get`, `attachments.get`, `labels.list` **and** metadata-only reads (no extra scope needed)?
- [ ] V5 — Quota/latency: `messages.list` and `messages.get` are 5 units each; measure a 25-hit search end-to-end before considering batching.
- [ ] V6 — Does the stored refresh token still refresh after being copied out of Key Vault (D9 assumes yes; if not, the credential model needs revisiting before implementation).

---

## 7. Out of scope (explicitly closed)

- Gmail writes: labels, read/unread, archive, delete, send (`modify_labels` exists in the client — unused by the CLI).
- Threads / conversation view (`show` + `rfc822msgid:` cover it for now).
- Filter-flag surface and any query DSL of our own; `GmailQueryBuilder` is not touched.
- Human-facing output formats (table, plain text, colour).
- Migrating `fetch_mails` / the bot's four consumers to the fixed parser.
- Docker image; MCP server wrapper; pi extension/custom tool (the CLI is the portable interface; a thin MCP wrapper can come later without changing anything above).
- Attachment upload to gdrive (rclone handles that; the CLI only writes locally).
- Search ranking beyond Gmail's own ordering: no re-ranking, no embeddings, no index.

## 8. Consequences worth remembering after this project

- The agent gains a mail tool only when `setup.sh` has run the new uv step **and** `SEAMAIL_GOOGLE_CREDENTIALS` is exported in the agent's shell — the second part lives outside git (token JSON in the password manager, exported per machine).
- `cli-requirements.txt` is a second dependency list; if it drifts from `pyproject.toml`, the CLI breaks in a way CI will not catch. A `setup.sh` reference (or a test asserting the direct deps of `pyproject.toml` are a subset) is cheap insurance — candidate ticket.
