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

- **N9** MIGRATE STEP that frees the stricter `Amount`: smallest form `quarantine amount`; waits for the fate slice and D036 (M3, M4, M5).

## Parked items touched, not decided

- **M8, M9** (D036): the trigger "before the record format v3 step" is reached at P2. P2 changes record keys only and avoids both (P5-18, By: Fable). M8 and M9 stay open.

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

- QV3-7 and QV3-8 moved to big after the plan check (see below).

**Big, added after the plan check** ([plan repair](../../../0004-generated-replay/workflow/2026-11-07/record-format-v3/plan.md#plan-repair-after-plan-check-2026-11-07)) → By: Fable (rulings O2, O3 under DL-144)

- **QV3-7** RESPONSE count line `N records, K checked, M rejected at capture`, then `digest not verified (P2b)` until P2b: A both lines only when M > 0 · B always. Default A (By: Opus, PLAN repair record-v3). Narrows the DL-136 wording "prints one count line".
- **QV3-8** A rejected RESPONSE RECORD (non-200, or 200 rejected at capture) skips: A the DL-102/DL-122 value checks only · B also the TYPE path check and the W2 version count; orphan (DL-040) and held checks read every record. Default B, per the DL-136 Because (an outage is not a TYPE change). Tests V22 (503), V23 (200 rejected), controls V24, V25.

**Deferred, not decided**

- DL-136 digest half (bad-digest records counted, not checked): follow-up step P2b, open item D035 (RV3-07, RV3-15).

## Several EFFECTS and module name (P3, P5)

Ledger: [0004 multi-effect-module](../../../0004-generated-replay/workflow/2026-11-07/multi-effect-module/decisions.md). Built defaults, open (DL-144).
By: Opus (PLAN multi-effect, default, open) for every line.

- **Q6E-1** Which sources take the stem module name: A every source (all byte pins move, re-pin sub-step) · C only a source with an ENTRY LINE, others stay `BeamlSpike`. Default C.
- **Q6E-2** `Rejected` namespace: A `<Module>.Rejected` (`Orders.Rejected`) · B one fixed `BeamlSpike.Rejected`. Default A.
- **Q6E-4** One EFFECT per flow: A yes (`place` cannot pay and store in one flow) · B several EFFECTS per flow, records selected by operation. Default A.
- Other Migrate default of this step, not big: **Q6E-3** `Replay.run(operation, ...)` with two or more EFFECTS. Default A.

## Database transports (P4)

Plan: [db-transport/plan.md](../../../0004-generated-replay/workflow/2026-11-07/db-transport/plan.md). Options: [db-transport/decisions.md](../../../0004-generated-replay/workflow/2026-11-07/db-transport/decisions.md). Every line: By: Opus (PLAN db-transport, default, open).

- **QDB-1** `db.get` key: A the key TYPE has one String field, its name is the key · B key in the call `db.get("records", order_id)`. Default A.
- **QDB-2** `BeamlDb` signatures: A `put(table, {type, version}, core)`, `get/3`, `list/3` · B the 0005 plan's `put/4`. Default A.
- **QDB-5** db call records: A stream `"responses"`, v3 core + `request`, output values · B own stream with row references. Default A.
- **QDB-6** db outcomes: A `"ok"` / `"failed"` + reason · B `"accepted"` / `"rejected"`. Default A; P2 names win.
- **QDB-7** ROW SNAPSHOT: A `rows.jsonl` beside `--stored` (+ `source: "db"`, `row_id`), meta `row_count` checked · B one mixed file. Default A.
- **Other (not big):** QDB-3 newest row wins on `db.get`; QDB-4 one bad row fails the whole `db.list`.
