# OWNER review: EXPERIMENT 0005 defaults (free run, DL-144)

**[Proposal]** PLAN phase, 2026-11-07. Every default below is built and stays open until the OWNER signs it off (DL-139). Details and options: [decisions.md](decisions.md).
By: Opus (PLAN exp0005, default, open) for every line.

## Big (syntax, record format or host-called name)

- **Q5-3** List TYPE: A `items: [Order]` field form · B `list OrderList of Order` keyword. Default A.
- **Q5-6** Module name: A from file stem (`Orders`) · B `module Orders` line. Default A.
- **Q5-9** List page load: A second ENTRY LINE `ui.orders`, called from `mount` · B new `ui.mount("orders")` transport. Default A.
- **Q5-8** Host DB module: A fixed `BeamlDb.put/4, list/3, get/3` · B configured module with a behaviour. Default A.
- **Q5-4** `--stored` over Postgres: A compiler runs `psql` (`--stored-db`) · B host task `mix beaml.stored` writes a row snapshot. Default B.
- **Q5-7** Capture streams: A JSONL files per run · B rows in the `records` table. Default A.
- **Q5-10** STORED ROW value shape: A bare projection in `value` · B record format v3 core in the row. Default B (DL-127, DL-143). By: Fable (default, open).
- **Q5-1** `db.get` key: A row `id` · B a TYPE field (`order_id`). Default B, not built in 0005.

## Other

- **Q5-2** `db.list` order and limit: A fixed in host (newest first, 100) · B fields in `OrderQuery`. Default A.
- **Q5-5** Generated code: A `app/lib/generated/orders.ex` in git · B Mix compiler into `_build`. Default A.

## Blocked, not decided

- **N9** MIGRATE STEP that frees the stricter `Amount`: smallest form `quarantine amount`; waits for the fate slice and D026 (M3, M4, M5).

## Parked items touched, not decided

- **M8, M9** (D026): the trigger "before the record format v3 step" is reached at P2. P2 changes record keys only and avoids both (P5-18, By: Fable). M8 and M9 stay open.

## Record format v3 (P2)

**[Proposal]** PLAN record-v3, 2026-11-07. Ledger: [record-format-v3](../../../0004-generated-replay/workflow/2026-11-07/record-format-v3/plan.md), options in its [decisions.md](../../../0004-generated-replay/workflow/2026-11-07/record-format-v3/decisions.md). Every line → By: Opus (PLAN record-v3, default, open).

**Big (record format)**

- **QV3-1** Format marker: A `version: 3` · B `format` key · C file name. Default A.
- **QV3-2** Span id: A one `span_id` · B `client_span_id`/`server_span_id` as extras · C `span_id` + `span_kind`. Default A.
- **QV3-3** Transport extras: A flat top level (`status`, `request`) · B nested `transport: {...}`. Default A.
- **QV3-4** RESPONSE `outcome`/`reason`: A status, then decode (`status`, `decode`, `constructor`; equals the live failure reason) · B status only. Default A. Wider than the DL-136 wording.
- **QV3-5** Old files: A one-time rewrite of the v2 fixtures, reader v3 only · B reader accepts v2 and v3. Default A.
- **QV3-6** Digest covers: A `redacted`, `unknown_keys`, `value` (D6B-58 unchanged) · B also `unknown_fields`, `outcome`, `reason`. Default A.

**Other**

- **QV3-7** RESPONSE count line `N records, K checked, M not replayable`: A only when M > 0 · B always. Default A. Narrow reading of DL-136.
- **QV3-8** A rejected RESPONSE RECORD skips: A the DL-102/DL-122 value checks only · B also the TYPE path check. Default A. Narrow reading of DL-136.

**Deferred, not decided**

- DL-136 digest half (bad-digest records counted, not checked): follow-up step P2b (RV3-07, Repair, By: Opus).
