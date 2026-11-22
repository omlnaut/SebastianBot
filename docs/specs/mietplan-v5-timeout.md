# V5 — whole-webdepot resync against the Functions execution timeout

Verification item V5 from `docs/specs/mietplan-cli-session.md` §5, settled for ticket
#127 (`check_mietplan` resync route). Recorded, not measured: this machine has no Azure
login, no Key Vault, no Google token and no portal credentials, so no live run was made.

## What was checked

- `host.json` has **no `functionTimeout`**, so the runtime default applies to every
  function in the app:
  - **Consumption plan: 5 minutes** (and the HTTP front end caps a single response at
    **230 seconds** regardless of `functionTimeout`).
  - **Premium or Dedicated/App Service plan: 30 minutes** (adjustable, up to unbounded
    for App Service plans).
- The deployment plan is not recorded in the repo. `notes/dev_setup/general.md` only
  says the app was created in the Azure portal; `cloud/helper/eventgrid_wiring/azure_config.json`
  names it (`Sebastian`, `germanywestcentral`) but not its plan. So which default applies
  is **unconfirmed** and must be read from the portal (Function App → Configuration →
  "Plan type") by whoever owns the deployment.

## Cost estimate for `maxFileAge=all`

Work per run, with `F` folders and `N` files in the portal:

| Step | Requests |
| --- | --- |
| Walk | about `2F` portal requests (`getFolders` + `getFiles` per folder) |
| Per file | 1 portal download, 1 Drive path lookup, 1 Drive create/update |

So wall time ≈ `2F × t_portal + N × (t_download + t_lookup + t_upload)`.

With invoice-sized PDFs and a hobby-portal/Drive latency of roughly 0.5–1 s per request
(the unauthenticated `getFolders` probe in V1 answered quickly, but no authenticated
latency was measurable), the first term already costs 100 s at `F = 100`. At
`N = 200` files the per-file term alone is 300–600 s. A whole-webdepot run therefore
**plausibly exceeds the 5-minute Consumption default and the 230-second HTTP response
cap**, and only fits a 30-minute Dedicated/Premium window for a small tree. These are
estimates from request counts, not measurements.

## Finding

A whole-webdepot (`maxFileAge=all`) resync is not guaranteed to finish inside the
Functions timeout, and on a Consumption plan its JSON report can be cut off by the
230-second HTTP response cap even if the function itself keeps running. The walk also
runs strictly (raises on the first unreadable folder), so a timeout is reported as a
missing response rather than as a per-file failure.

## Practical mitigation (no deployment change)

- **Folder scope is the repair tool.** `folder=<path-prefix>` resyncs one subtree, which
  keeps a repair run inside any of these windows. A failed night is normally one subtree,
  not the whole depot.
- **The timer keeps the one-day window**, so the nightly run never approaches the limit
  (it downloads only a day's files, as it already does today).
- A timed-out run is **safe to repeat**: writes are upserts, nothing is ever deleted, and
  files written before the cutoff stay written. Re-run with a narrower `folder` to finish.
- `durationSeconds` in the response is the measured cost of the run that did finish; the
  first successful whole-webdepot run on the real deployment is the measurement that
  would replace the estimate above.

## `host.json`

**Unchanged.** Raising `functionTimeout` would not help on Consumption (5 minutes is the
plan maximum) and the 230-second HTTP cap is unaffected by it; on Premium/Dedicated the
30-minute default already leaves the mitigations above as the real answer. Changing it is
a deployment-wide decision for the owner, outside this ticket.
