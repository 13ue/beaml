# OWNER review: EXPERIMENT 0005 defaults (free run, DL-144)

**[Proposal]** PLAN phase, 2026-11-07. Every default below is built and stays open until the OWNER signs it off (DL-139). Details and options: [decisions.md](decisions.md).
By: Opus (PLAN exp0005, default, open) for every line.

## Big (syntax, record format or host-called name)

- **Q5-3** List TYPE: A `items: [Order]` field form · B `list OrderList of Order` keyword. Default A.
- **Q5-6** Module name: A from file stem (`Orders`) · B `module Orders` line. Default A.
- **Q5-9** List page load: A second ENTRY LINE `ui.orders`, called from `mount` · B new `ui.mount("orders")` transport. Default A.
- **Q5-8** Host DB module: A fixed `BeamlDb.put/3, list/3, get/3` (`put(table, {type, version}, json)`, QDB-2) · B configured module with a behaviour. Default A. Corrected from put/4 on 2026-11-07 (plan re-check R3). → By: Fable · Repair
- **Q5-4** `--stored` over Postgres: A compiler runs `psql` (`--stored-db`) · B host task `mix beaml.stored` writes a row snapshot. Default B.
- **Q5-7** Capture streams: A JSONL files per run · B rows in the `records` table. Default A.
- **Q5-10** STORED ROW value shape: A bare projection in `value` · B record format v3 core in the row. Default B (DL-127, DL-143). By: Fable (default, open).
- **Q5-1** `db.get` key: A row `id` · B a TYPE field (`order_id`). Default B, not built in 0005.
- **QDB-6b** (P4) A failed db call is a rejected record with its reason. Challenge: http writes no record on a transport failure. Default yes. [Detail](../../../0004-generated-replay/workflow/2026-11-07/db-transport/decisions.md#qdb-6b--migrate--big--a-failed-db-call-is-a-rejected-record-with-its-reason). → By: Fable (default, open)
- **QDB-8** (P4, 0005) The chained read over rows (N7/N7b) under the built D6B-39: A block N7/N7b on M4 · B a String-only ROW TYPE `Note { text: String }` with its own chain · C open M4 now. Default B. [Detail](../../../0004-generated-replay/workflow/2026-11-07/db-transport/decisions.md#qdb-8--migrate--big--0005-n7-and-n7b-under-d6b-39). → By: Fable (default, open)
- **PDB-18** (P4) `unknown_fields` of a `db.list` record: `items.<i>.<field>`. [Detail](../../../0004-generated-replay/workflow/2026-11-07/db-transport/decisions.md#undo-and-repair-decisions). → By: Fable (flag)
- **PDB-24** (P4) rows count line `rows: N rows, K checked, M not decodable`. [Detail](../../../0004-generated-replay/workflow/2026-11-07/db-transport/decisions.md#undo-and-repair-decisions). → By: Fable (flag)
- The four P4 lines above moved here from "Database transports (P4)" on 2026-11-07 (plan re-check R3); pointers stay there. → By: Fable · Repair

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

**After the plan check** ([plan repair](../../../0004-generated-replay/workflow/2026-11-07/multi-effect-module/plan.md#plan-repair-after-plan-check-2026-11-07)), 2026-11-07

- Variants keep the stem `orders` in their own directories; N10 gets a `defmodule Orders do` control (D6B-210). → By: Fable · Repair
- N13 compares against the P3 base commit, moved with any pin sub-step (D6B-212). → By: Fable · Repair
- **Q6E-2** stays big and open. The docs phase notes under DL-133 that `BeamlSpike.Rejected` named the shape; the generated name is `<Module>.Rejected` (D6B-213). → By: Fable · Undo

## Database transports (P4)

Plan: [db-transport/plan.md](../../../0004-generated-replay/workflow/2026-11-07/db-transport/plan.md). Options: [db-transport/decisions.md](../../../0004-generated-replay/workflow/2026-11-07/db-transport/decisions.md). Every line: By: Opus (PLAN db-transport, default, open).

- **QDB-1** `db.get` key: A the key TYPE has one String field, its name is the key · B key in the call `db.get("records", order_id)`. Default A.
- **QDB-2** `BeamlDb` signatures: A `put(table, {type, version}, core)`, `get/3`, `list/3` · B the 0005 plan's `put/4`. Default A.
- **QDB-5** db call records: A stream `"responses"`, v3 core + `request`, output values · B own stream with row references. Default A.
- **QDB-6** db outcomes: A `"ok"` / `"failed"` + reason · B `"accepted"` / `"rejected"`. Default A; P2 names win.
- **QDB-7** ROW SNAPSHOT: A `rows.jsonl` beside `--stored` (+ `source: "db"`, `row_id`), meta `row_count` checked · B one mixed file. Default A.
- **Other (not big):** QDB-3 newest row wins on `db.get`; QDB-4 one bad row fails the whole `db.list`.

**After the plan check** ([plan repair](../../../0004-generated-replay/workflow/2026-11-07/db-transport/plan.md#plan-repair-after-plan-check-2026-11-07)), 2026-11-07

- **QDB-6** withdrawn. The P2 words `accepted` / `rejected` hold; reasons `transport`, `decode`, `constructor`, `not_found`. → By: Fable · Repair
- **QDB-6b** (big): see "## Big" above.
- **QDB-2** (big) now `put(table, {type, version}, json)`: the generated code encodes the core with OTP `:json`; `get`/`list` return JSON binaries. Q5-8 reads put/3. → By: Fable · Repair
- **PDB-18** (big): see "## Big" above.
- **PDB-24** (big): see "## Big" above.
- **QDB-8** (big): default B, see "## Big" above. The earlier default A (By: Opus, PLAN repair P3/P4) is replaced by the ruling B (By: Fable).

**Parked items touched, not decided (P4)**

- **M4** (D036): PDB-09 withdrawn; D6B-39 holds for ROW TYPES; N18 pins today's help text, no new wording. 0005 N7/N7b run on the String-only ROW TYPE `Note` under QDB-8 B; the real `Order` chain waits on M4. → By: Fable · Repair

**P4b RED defaults (`--stored` over rows)**, 2026-11-08. Ledger: [red-plan.md P4b](../../../0004-generated-replay/workflow/2026-11-07/db-transport/red-plan.md#p4b---stored-over-the-row-snapshot). By: Opus (RED db-stored, default, open) for every line.

- **Orphan rows (DL-040 parity):** A row blocks with the DL-040 ROW text when its `operation` has no EFFECT and no RETIRE LINE and its `type.name` has no reader · B block on operation only (the RESPONSE form; a removed writer with a kept reader blocks) · C never block, count as not decodable. Default A. The RETIRE LINE free stays blocked on M5.
- **Off-chain row:** A an accepted row of a ROW TYPE with a TYPE VERSION on no chain blocks with the path text (N20, N20b) · B counted as not decodable (the plan line "every other row is counted"). Default A.
- **Rows count line:** A `rows: N rows, K checked, M not decodable` prints on every success, also with M = 0 · B QV3-7 A (only when M > 0). Default A; the P2 RESPONSE pair keeps QV3-7 A.

**P4 GREEN defaults**, 2026-11-08. Ledger: [green-output.md](../../../0004-generated-replay/workflow/2026-11-07/db-transport/green-output.md). By: Opus (GREEN db-transport, default, open) for every line.

- **Constructor field in a ROW TYPE** (big, syntax rule): the first signature of the constructor takes exactly its String fields, else a build error (`... needs a first signature that takes the String fields of Amount; a row stores the field values (PDB-13)`). Reason: the encode writes the struct fields and the decode reads the first matching signature, so any other constructor cannot be read back. Options: A this rule · B encode by signature names (needs a field-to-parameter map) · C allow it and lose rows. Default A.
- **`BeamlDb` reserved as a module name** (big, host-called name): a stem `beaml_db` gives `error: ... gives the module BeamlDb, which the generated code calls`. Same rule as D6B-203; `System` added too (TEST O1).
- **ROW TYPE fields** (not big): String, literal enums with a keep-value variant, constructor records only, the http output rule. The plan also listed Int and nested plain records; they are a build error (`slice 1 decodes String fields only`). Default: as built.
- **Orphan row help line**: the DL-040 help (`declare: retire <op> keep <n> days`) is printed, and a RETIRE LINE frees the rows (they are then counted, not checked). This follows the RED orphan default A; the RETIRE LINE meaning for rows stays M5.
- **No DL-101 shape check over stored rows**: `--stored` checks path, literals and constructors; a row with a missing field passes the build and fails `db.list` at run time (`decode`).

## First question tomorrow: M4 (D036)

- **QDB-8** (big): the chained read over rows (N7/N7b) runs on a String-only ROW TYPE because the built D6B-39 bans constructor and enum fields in a chained TYPE. The real `Order` chain waits on M4 (help text vs lifting D6B-39). Default B, By: Fable (default, open). Options: A block N7/N7b on M4 · B String-only ROW TYPE · C answer M4 now.

## Slice 6d built defaults

- **G6D-04** A pure ENTRY LINE target in a source with an outbound EFFECT writes no ENTRY RECORD and has no `Replay.entry`. UI events of that target reach no `--stored` check and no REPLAY RUN. Challenge (TEST O2): the D6B-136 reason (no `Replay` module) does not hold there. → By: Opus (GREEN slice6d, default, open) · Repair (raised from Undo by TEST O2, Fable)
- **G6D-03** The ENTRY RECORD `type` key lists the fields in source order; a RESPONSE RECORD sorts them. The fingerprint sorts in both. → By: Opus (GREEN slice6d, default, open) · Repair
- **G6D-12** The input TYPE needs a keep-value variant for a literal enum field and `name: String` constructor signatures, with the outbound texts in the `effect <op>:` form. No test pins it. → By: Opus (GREEN slice6d, default, open) · Undo

## Database transports P4a, RED text defaults (added after the RED review)

- **order_v2 error text** names `orders.save` and `Order.amount` (built D6B-39 text for a chained row TYPE with a constructor field). By: Opus (RED db-transport, default, open).
- **N25b error text** names `TYPE Order v1` and the field `channel` (DL-122 text for a list item). By: Opus (RED db-transport, default, open).

## Count-line print rule: one question for both streams (merged after the P4b RED review)

- **QV3-7 / rows count line**: RESPONSE RECORDS print the two count lines only when M > 0 (QV3-7 A); ROW SNAPSHOTS always print `rows: N rows, K checked, M not decodable` (P4b default A). One rule should decide both: is a printed count the proof that the check ran (always print, B for records), or is silence the normal case (A for both, then N20b loses its "3 checked" proof)? By: Fable (merged question, default: as built, open).

## 0005 RED defaults

2026-11-08. Ledger: [red-plan.md](../2026-11-08/red-plan.md). By: Opus (RED exp0005, default, open) for every line.

- **Snapshot record set** (big, what `--stored` reads): A `mix beaml.stored` writes an empty `responses.jsonl`; the build checks the STORED ROWS only, the per-run capture records (Q5-7 A) are not a store · B also copy the capture `responses.jsonl` of earlier runs. Default A.
- **`mix beaml.stored DIR`** (big, host-called name): A one argument, the snapshot directory; run.py runs the compiler · B `mix beaml.stored SOURCE` runs the compiler itself (Q5-4 B text). Default A.
