# Session export — `seamail draft`, agent-facing Gmail draft creation

- **Date:** 2026-10-31
- **Kind:** grilling session, followed by implementation in the same sitting (branch `seamail/drafts`, issue #120).
- **Predecessor:** `docs/specs/gmail-cli-session.md` — the read-only `search`/`show`/`labels`/`attachments` CLI. This document **supersedes its D3 ("no Gmail writes at all") for draft creation only**; every other decision there stands.
- **Origin of the need:** the agent can read mail but not answer it. Drafting is the useful half of writing: compose into Drafts, let the human review and send.

---

## 1. Facts established by running code (not read, not assumed)

A throwaway script against the live mailbox settled these before any decision was taken:

- The credential already in `~/.seamail.credentials` carries `gmail.modify`, which is sufficient for `drafts.create`, `drafts.delete` **and** for `messages.get`/`attachments.get` on a draft's message. **No new scope, no re-authorisation.**
- `drafts.create` with `body={"message": {"raw": base64url(MIME), "threadId": ...}}` creates the draft and returns `{"id": <draftId>, "message": {"id": <messageId>, "threadId": ..., "labelIds": ["DRAFT"]}}`.
- Passing `threadId` attaches the draft to the existing thread (observed: thread message count 1 → 2), and `In-Reply-To`/`References` survive verbatim.
- `From` is filled by Gmail from the authenticated account (`Oliver Rüger <oneironaut.oml@gmail.com>`); the CLI never sets it.
- The draft's `messageId` is an ordinary message: `messages.get(format="full")` returns its headers **and** body, so the existing `seamail show <messageId>` verifies a draft with no new read path.
- `email.message.EmailMessage` with the default policy produces the raw MIME correctly, including RFC 2047 subjects and RFC 2231 attachment filenames.

## 2. Decisions

- **D1 — Add-only.** The shipped CLI may **create** a draft and nothing else: no send, no delete, no relabel, no modify. This is a *structural* guarantee — the send API is never called anywhere in the package, and a unit test fails if `messages().send` or `drafts().send` appears in `cli/` or `sebastian/`. Draft cleanup after a mistake is the human's click. Rationale: one testable invariant ("this tool cannot remove or send anything") instead of a policy the code could drift away from.
- **D2 — Surface.** Flat verb, consistent with `search`/`show`/`labels`/`attachments`, one entry point (`python -m cli.mail draft`):

  ```
  seamail draft --to <addr[,addr]> [--cc …] [--bcc …] [--subject S]
                [--body-file P | < body on stdin]
                [--attach P]… [--attach-name <base>=<new>]…
                [--reply-to <message-id> [--all]]
                [--dry-run]
  ```
- **D3 — Body.** `text/plain` only, UTF-8, never in argv: stdin by default, `--body-file <path>` as the alternative. Multi-paragraph German prose through shell quoting is the failure mode this avoids. No HTML alternative, no signature handling.
- **D4 — Replies in v1.** `--reply-to <message-id>` fills `To` from the original sender, `Subject` as `Re: …` (not doubled), `threadId`, `In-Reply-To` and `References` (original References + Message-Id). `--all` additionally adds the original To+Cc, minus the account's own address (`users.getProfile`), minus duplicates. `--all` without `--reply-to`, or `--to` together with `--reply-to`, is a usage error.
- **D5 — Attachments in v1.** Repeatable `--attach <path>`, filename = local basename; `--attach-name <basename>=<newname>` is an **order-free rename map** (positional pairing across two repeatable flags mispairs on reorder and forces naming every file to rename one). Unknown key = usage error. Duplicate resulting filenames = usage error (never a silent rename). Renamed names may contain umlauts and spaces but not path separators, control characters, or nothing at all.
- **D6 — Failure classification.** Missing `--to`, unparseable address, `CR`/`LF` in any header value (injection guard), unknown `--attach-name` key, duplicate attachment filename, `--all` without `--reply-to`: usage error, exit 2. Nonexistent attachment path: usage error. Unreadable file or zero-byte attachment: io error, exit 1. Oversized message: usage error naming each file's size and the limit.
- **D7 — Size cap.** Gmail's cap is 25 MB *after* base64 (≈4/3 inflation), so the check is on the encoded MIME length, pre-flight, before any API call. Gmail's own rejection ("Request too large") is opaque; ours names the files.
- **D8 — `--dry-run`.** Full validation and MIME construction, JSON echo of headers, body length, attachment names/sizes and encoded size, **zero** Gmail writes. Also the network-free target for tests.
- **D9 — Verification path.** `draft` returns `draftId` + `messageId` + `threadId`; the agent re-reads with the existing `seamail show <messageId>`, and pulls an attachment back out with `seamail attachments <messageId>` to compare a checksum. No `draft show`, no second read implementation.
- **D10 — Layering.** MIME construction, address/attachment validation and reply derivation live in `sebastian/clients/google/gmail/compose.py` (pure functions, no argv, no API) so the bot can reuse them; `GmailServiceWrapper.create_draft(raw, thread_id)` and `.fetch_reply_context(message_id)` are thin API adapters; models (`DraftRequest`, `OutgoingAttachment`, `ComposedDraft`, `CreatedDraft`, `ReplyContext`, `ReplyTarget`) live in `sebastian/domain/gmail.py`; `cli/mail.py` only does argv → request → JSON, and its service protocol is honestly named `GmailService` now that it is not read-only.
- **D11 — Artifact.** This document (a sibling of the read-only export, which is left verbatim: it is a dated record and editing its D3 would falsify it), issue #120, branch `seamail/drafts` off `seamail/integration`, pushed without a merge.

## 3. Contract

```
seamail draft [--to A[,B]] [--cc …] [--bcc …] [--subject S]
              [--body-file P] [--attach P]… [--attach-name base=new]…
              [--reply-to ID] [--all] [--dry-run]
```

```jsonc
// success
{ "command": "draft", "dryRun": false,
  "draft": { "id": "r-…", "messageId": "1a…", "threadId": "1a…" },   // null when --dry-run
  "message": { "to": ["…"], "cc": [], "bcc": [],
               "subject": "…", "bodyChars": 412,
               "attachments": [{ "path": "/tmp/x.pdf", "filename": "Rechnung Oktober.pdf",
                                 "mimeType": "application/pdf", "size": 91234 }],
               "encodedBytes": 132480 } }

// error (stderr) — kinds: auth | api | usage | io
{ "command": "draft", "error": { "kind": "usage", "message": "…" } }
```

Exit codes: `0` ok, `1` runtime/io/api, `2` usage. `bcc` appears in the echo but recipients never see it.

## 4. Verification performed

- Unit tests: `tests/unit_tests/clients/test_gmail_compose.py` (MIME shape, RFC 2047 subject, RFC 2231 filename, rename map, duplicate names, size cap, reply derivation, injection guard), `tests/unit_tests/cli/test_mail_cli.py` (envelope, dry-run makes no create call, usage/io/api error mapping, body from stdin and from file), `tests/unit_tests/cli/test_no_send.py` (add-only guard).
- Live: two drafts left in the mailbox for the human (one new mail with a real PDF renamed through `--attach-name`, one threaded reply with an umlaut subject and an attachment), each read back with `seamail show`, and the attachment round-tripped out of the draft with `seamail attachments` and compared by sha256.

## 5. Out of scope (explicitly closed)

- **Sending.** Not implemented, and not to be implemented as "the obvious next step" — it is the human's call, and `Reference/Agent-context.md` in the vault records that.
- Deleting, updating or relabelling drafts; `drafts.update`.
- HTML bodies, inline images, signatures, templates.
- Contacts/address-book lookup: recipients come from prior mail (`seamail search`) or the human.
- Bot-side adoption (`usecases/` keeps its own writerless mail path for now).
