# OWNER walk-through: EXPERIMENT 0005 built defaults (DL-144)

**[Proposal]** Clean walk-through for the OWNER, written 2026-11-08 after the 0005 TEST PASS ([review](../2026-11-08/review.md)). Register entry: D037 in [Decisions to be made](../../../../wiki/planning/decisions-to-be-made.md#d037--experiment-0005-built-defaults-dl-144-walk-through). Every default below is built and stays open until the OWNER signs it off (DL-139, DL-144). Nothing here is decided.
Order and grouping: By: Opus (docs exp0005). Each line keeps the author of its default. Option letters marked "(letters: docs)" were written by the docs pass where the ledger gave none.
The original text stays unchanged below the line ([history](#history-unchanged-text-2026-11-07-to-2026-11-08)). Details and options per step sit in the linked ledgers.

Line format: **ID** · one sentence · options · built default · `By:`.

## Big, first

### 1 · M4 (D036), critical path

→ **M4** · A chained ROW TYPE may not hold a constructor or enum field (D6B-39), so the real `Order` chain cannot run. · A the DL-102 help names "restore the previous clause or literal" · B lift D6B-39 before any FATE OPERATION. · Built: none; D6B-39 holds, N18 pins today's help text, N7/N7b run on the String-only `Note` (QDB-8 B). · By: OWNER parked (D036); built state by Fable (Repair).
⠀⠀↳ It blocks the `Order` chain and, with M3 and M5, the fate slice (N9).

### 2 · How a page renders a BEAML value (host-called name)

→ **GREEN exp0005 encoder** · The list page calls the compiler-internal `Orders.__beaml_encode_order/1`. · A host calls the generated encoder · B host matches the enum tuple itself · C compiler emits a public `project_<type>/1` (TEST O3). · Built: A. · By: Opus (GREEN exp0005, default, open); C made concrete by Opus (TEST exp0005).

### 3 · Q5-10 STORED ROW value shape

→ **Q5-10** · What a row holds in `value`. · A the bare projection · B the record format v3 core in the row (DL-127, DL-143). · Built: B. · By: Fable (default, open).

### 4 · Q6E-1, Q6E-2 module and `Rejected` names

→ **Q6E-1** · Which sources take the stem module name. · A every source (all byte pins move) · C only a source with an ENTRY LINE. · Built: C. · By: Opus (PLAN multi-effect, default, open).
→ **Q6E-2** · The namespace of the `Rejected` struct. · A `<Module>.Rejected` (`Orders.Rejected`) · B one fixed `BeamlSpike.Rejected`. · Built: A. · By: Opus (PLAN multi-effect, default, open).

### 5 · QDB-6b, QDB-8 database failures and the chained read

→ **QDB-6b** · A failed db call writes a rejected record with its reason; http writes none on a transport failure. · A yes, a rejected record · B no record, as http (letters: docs). · Built: A. · By: Fable (default, open).
→ **QDB-8** · The chained read over rows (N7/N7b) under D6B-39. · A block N7/N7b on M4 · B String-only ROW TYPE `Note` with its own chain · C answer M4 now. · Built: B. · By: Fable (default, open).

### 6 · Record format v3 (QV3-1 to QV3-8)

→ **QV3-1** · Format marker. · A `version: 3` · B a `format` key · C the file name. · Built: A. · By: Opus (PLAN record-v3, default, open).
→ **QV3-2** · Span id. · A one `span_id` · B client and server span ids as extras · C `span_id` plus `span_kind`. · Built: A. · By: Opus (PLAN record-v3, default, open).
→ **QV3-3** · Transport extras. · A flat top level (`status`, `request`) · B nested `transport: {...}`. · Built: A. · By: Opus (PLAN record-v3, default, open).
→ **QV3-4** · RESPONSE `outcome`/`reason`. · A status, then decode (equals the live failure reason) · B status only. · Built: A, wider than the DL-136 wording. · By: Opus (PLAN record-v3, default, open).
→ **QV3-5** · Old files. · A one-time rewrite of the v2 fixtures, reader v3 only · B reader accepts v2 and v3. · Built: A. · By: Opus (PLAN record-v3, default, open).
→ **QV3-6** · What the digest covers. · A `redacted`, `unknown_keys`, `value` · B also `unknown_fields`, `outcome`, `reason`. · Built: A. · By: Opus (PLAN record-v3, default, open).
→ **QV3-7** · When the RESPONSE count lines print. · A only when M > 0 · B always. · Built: A (see item 7). · By: Opus (PLAN repair record-v3), raised to big by Fable.
→ **QV3-8** · What a rejected RESPONSE RECORD skips. · A the DL-102/DL-122 value checks only · B also the TYPE path check and the W2 version count. · Built: B. · By: Opus (PLAN repair record-v3), raised to big by Fable.

### 7 · The count-line print rule (one rule for both streams)

→ **QV3-7 / PDB-24** · RESPONSE RECORDS print counts only when M > 0; ROW SNAPSHOTS always print `rows: N rows, K checked, M not decodable`. · A silence is normal (both only when M > 0; N20b loses its proof) · B a printed count proves the check ran (both always). · Built: split (A for records, B for rows). · By: Fable (merged question, default, open); rows line by Opus (RED db-stored, default, open).

### 8 · The row shape check (P4c)

→ **P4c** · A stored row or RESPONSE RECORD with a missing or wrong-type String field passes `--stored` and fails `db.list` at run time. · A block the build with the DL-102 text · B count it as not decodable. · Built: A in progress (RED `b15c1e6d`, GREEN running). · By: Fable (default, open).

### 9 · ENTRY RECORD (G6D-03, G6D-04)

→ **G6D-04** · A pure ENTRY LINE target in a source with an outbound EFFECT writes no ENTRY RECORD and has no `Replay.entry`. · A as built · B write the ENTRY RECORD there too (letters: docs). · Built: A. · By: Opus (GREEN slice6d, default, open); raised to Repair by Fable (TEST O2).
→ **G6D-03** · The ENTRY RECORD `type` key lists fields in source order; a RESPONSE RECORD sorts them. · A source order · B sorted, as the RESPONSE RECORD (letters: docs). · Built: A. · By: Opus (GREEN slice6d, default, open).

## Other defaults

Marked "(big)" where the ledger marked it big; the class is not lowered here.

### 0005 PLAN

→ **Q5-1 (big)** · `db.get` key. · A row `id` · B a TYPE field. · Built: B in P4 (QDB-1 A), unused in 0005. · By: Opus (PLAN exp0005, default, open).
→ **Q5-2** · `db.list` order and limit. · A fixed in the host (newest first, 100) · B fields in `OrderQuery`. · Built: A. · By: Opus (PLAN exp0005, default, open).
→ **Q5-3 (big)** · List TYPE. · A `items: [Order]` field form · B a `list` keyword. · Built: A. · By: Opus (PLAN exp0005, default, open).
→ **Q5-4 (big)** · `--stored` over Postgres. · A compiler runs `psql` · B host task `mix beaml.stored` writes a snapshot. · Built: B. · By: Opus (PLAN exp0005, default, open).
→ **Q5-5** · Generated code. · A `app/lib/generated/orders.ex` in git · B a Mix compiler into `_build`. · Built: A. · By: Opus (PLAN exp0005, default, open).
→ **Q5-6 (big)** · Module name. · A from the file stem · B a `module` line. · Built: A. · By: Opus (PLAN exp0005, default, open).
→ **Q5-7 (big)** · Capture streams. · A JSONL files per run · B rows in `records`. · Built: A. · By: Opus (PLAN exp0005, default, open).
→ **Q5-8 (big)** · Host DB module. · A fixed `BeamlDb.put/3, list/3, get/3` · B a configured module with a behaviour. · Built: A. · By: Opus (PLAN exp0005, default, open); put/3 by Fable (Repair).
→ **Q5-9 (big)** · List page load. · A a second ENTRY LINE `ui.orders` from `mount` · B a new `ui.mount` transport. · Built: A. · By: Opus (PLAN exp0005, default, open).

### P3, P5 several EFFECTS

→ **Q6E-4 (big)** · One EFFECT per flow. · A yes · B several EFFECTS per flow. · Built: A. · By: Opus (PLAN multi-effect, default, open).
→ **Q6E-3** · `Replay.run(operation, ...)` with two or more EFFECTS. · A as built (letters as in the ledger). · Built: A. · By: Opus (PLAN multi-effect, default, open).

### P2 record format

→ **D035 (P2b)** · The DL-136 digest half: a bad `value_sha256` is counted, not checked. · Build in step P2b · leave open. · Built: not built; P2 prints `digest not verified (P2b)`. · By: Fable (ruling O3 under DL-144), class Repair.

### P4 database transports

→ **QDB-1** · `db.get` key form. · A the key TYPE has one String field · B key in the call. · Built: A. · By: Opus (PLAN db-transport, default, open).
→ **QDB-2 (big)** · `BeamlDb` signatures. · A `put(table, {type, version}, json)`, `get/3`, `list/3` · B `put/4`. · Built: A. · By: Opus (PLAN db-transport, default, open); JSON by Fable (Repair).
→ **QDB-3** · Newest row wins on `db.get`. · A as built (letters: docs). · Built: A. · By: Opus (PLAN db-transport, default, open).
→ **QDB-4** · One bad row fails the whole `db.list`. · A as built (letters: docs). · Built: A. · By: Opus (PLAN db-transport, default, open).
→ **QDB-5** · db call records. · A stream `responses`, v3 core plus `request` · B own stream with row references. · Built: A. · By: Opus (PLAN db-transport, default, open).
→ **QDB-7** · ROW SNAPSHOT. · A `rows.jsonl` beside `--stored`, meta `row_count` checked · B one mixed file. · Built: A. · By: Opus (PLAN db-transport, default, open).
→ **PDB-18 (big)** · `unknown_fields` of a `db.list` record use `items.<i>.<field>`. · A as built (letters: docs). · Built: A. · By: Fable (flag).
→ **Orphan rows** · A row of an operation with no EFFECT and no RETIRE LINE. · A block with the DL-040 ROW text · B block on operation only · C count as not decodable. · Built: A. · By: Opus (RED db-stored, default, open).
→ **Off-chain row** · An accepted row of a TYPE VERSION on no chain. · A block with the path text · B count as not decodable. · Built: A. · By: Opus (RED db-stored, default, open).
→ **order_v2 error text** · Names `orders.save` and `Order.amount` (D6B-39 text). · A as built (letters: docs). · Built: A. · By: Opus (RED db-transport, default, open).
→ **N25b error text** · Names `TYPE Order v1` and the field `channel` (DL-122 text). · A as built (letters: docs). · Built: A. · By: Opus (RED db-transport, default, open).
→ **Constructor field in a ROW TYPE (big)** · The first constructor signature takes exactly its String fields. · A this rule · B encode by signature names · C allow it and lose rows. · Built: A. · By: Opus (GREEN db-transport, default, open).
→ **`BeamlDb` reserved (big)** · A stem `beaml_db` is a build error; `System` too. · A as built (letters: docs). · Built: A. · By: Opus (GREEN db-transport, default, open).
→ **ROW TYPE fields** · String, literal enums with a keep-value variant, constructor records only. · A as built (letters: docs). · Built: A. · By: Opus (GREEN db-transport, default, open).
→ **Orphan row help line** · The DL-040 help is printed; a RETIRE LINE frees the rows. · A as built (letters: docs). · Built: A; the meaning stays M5. · By: Opus (GREEN db-transport, default, open).
→ **No DL-101 shape check over rows** · Superseded by item 8 (P4c). · By: Opus (GREEN db-transport, default, open).

### P4c row shape check

→ **P4c block text** · One text for a missing key and a non-String value. · A one text · B two texts. · Built: A (RED). · By: Opus (RED P4c, default, open).

### Slice 6d

→ **G6D-12** · A literal enum field of the input TYPE needs a keep-value variant and `name: String` signatures. · A as built (letters: docs). · Built: A, no test pins it. · By: Opus (GREEN slice6d, default, open).

### 0005 RED

→ **Snapshot record set (big)** · What `--stored` reads. · A an empty `responses.jsonl`, STORED ROWS only · B also the capture records of earlier runs. · Built: A. · By: Opus (RED exp0005, default, open).
→ **`mix beaml.stored DIR` (big)** · The host task argument. · A the snapshot directory · B the source, and the task runs the compiler. · Built: A. · By: Opus (RED exp0005, default, open).

### 0005 GREEN and TEST

→ **`BeamlDb.get/3` key (big)** · Key match on the raw stored JSON. · A containment `@>`, newest row, `{:ok, nil}` · B one field per call with a unique index. · Built: A, unused. · By: Opus (GREEN exp0005, default, open).
⠀⠀↳ TEST O2: misses migrated fields.
⠀⠀↳ TEST O2: empty key returns any row.
→ **Notes page (big)** · One page `/notes` with form and list. · A one page, reload after submit · B `/notes/new` and `/notes`. · Built: A. · By: Opus (GREEN exp0005, default, open).
→ **TEST O1** · `run.py run` truncates `proto_dev` and checks the shipped `orders.ex` against 0 rows. · A keep the reset, the README says so · B a separate dev-rows build step. · Built: A. · By: Opus (TEST exp0005, open).

## Parked by the OWNER (D036)

→ **M3** · Fate forms and DL-116; needs a fresh explanation first. · By: OWNER parked.
→ **M4** · See Big item 1. · By: OWNER parked.
→ **M5** · `retire` meaning, also for rows (N28b pin, orphan help). · By: OWNER parked.
→ **M8** · Failure struct at the host; P2 avoided it (P5-18). · By: OWNER parked.
→ **M9** · Record lines in a block text; P2 avoided it. · By: OWNER parked.
→ **N9** · `quarantine amount` frees the stricter `Amount`; blocked until the fate slice. · By: OWNER parked (via M3, M4, M5).

## Answered

→ DL-126: declarative for shape and policy. · By: 13ue.
→ DL-127 to DL-129: one JSONB table, UI entry as inbound EFFECT, three db transports. · By: 13ue.
→ DL-130 to DL-134: ENTRY LINE, `ui_<event>/1`, `//` comments, `Rejected`, `--stored` over entries. · By: 13ue.
→ DL-137, DL-139, DL-141 to DL-143: one `migrate` block, defaults rule, ENTRY RECORD, one record format. · By: 13ue.
→ DL-144: free run for 0005, walk-through next day. · By: 13ue.
→ DL-147: a RED file joins `run.py` in its GREEN commit. · By: Fable.
→ QDB-6 withdrawn: `accepted`/`rejected` and the P2 reasons hold. · By: Fable (Repair).

---

## History (unchanged text, 2026-11-07 to 2026-11-08)

The text below is the review list as the workers wrote it. It is append-only; do not edit it.

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

## Row shape check (raised to Migrate by the P4 TEST review, 2026-11-08)

- **Big · a stored row with a missing or wrong-type String field**: today `--stored` counts it as checked and the whole `db.list` fails at run time. Options: A block the build with the DL-102 text (the build sees it, as for every other stored-value rule); B count the row as not decodable and go on. Default A, built as the small step P4c (`N32_row_missing_string_field`). By: Fable (default, open). RESPONSE RECORDS have the same gap; P4c covers both streams or notes the second.
- **Small · the P4c block text**: one text for both faults (missing key and non-String value): `error: TYPE <T>: 1 stored ROW of table <t> has no String value for field <f>` (also `RESPONSE RECORD of operation <op>`), with the record source and the DL-102 help line. Alternative: two texts. By: Opus (RED P4c, default, open).

## 0005 GREEN defaults

2026-11-08. Ledger: [green-output.md](../2026-11-08/green-output.md). By: Opus (GREEN exp0005, default, open) for every line.

- **Big · how a page renders a BEAML value** (host API): A the host calls the generated encoder `Orders.__beaml_encode_order/1` (the DL-105 projection, the channel as its literal) · B the host matches the enum tuple itself · C the compiler emits a public projection function. Default A (smallest: no compiler change, the literal stays in BEAML).
- **Big · `BeamlDb.get/3` key** (host API, unused): A key map of domain fields, `value->'value' @>` containment, newest row, `{:ok, nil}` when none · B one field per call with a unique index (Q5-1 B text). Default A.
- **Big · the notes page** (page-visible): A one page `/notes` with form and list, reload (`push_navigate`) after a submit · B `/notes/new` and `/notes` as for orders. Default A.
