# Decisions: DB TRANSPORTS and `--stored` over STORED ROWS (EXPERIMENT 0005 prerequisite P4)

**[Proposal]** PLAN phase, 2026-11-07. Decisions that DL-127, DL-129, DL-137, DL-143 and the 0005 defaults (Q5-1 to Q5-10) do not settle.
Classes follow Decision4. DL-144 (free run): every Migrate question has a built default, pinned by a test in RED and GREEN, and stays open until the OWNER signs it off (DL-139 rule). "Big" marks a default that touches syntax, a record format or a host-called name; those are appended to the 0005 [owner-review.md](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md) under "Database transports (P4)".
Every entry carries a `By:` line (DL-107). Workers record each taken default again in their `notes.md`.
ID check: no `PDB-` or `QDB-` ID exists in `experiments/` or `wiki/` at this plan (grep). Parked D036 items (M3, M4, M5, M8, M9) are not decided here.

## OWNER questions (Migrate, default built)

### QDB-1 · Migrate · big · How `db.get` names its key

- **A.** The input TYPE of `db.get` has exactly one String field; that field name is the key; the ROW TYPE must hold a String field of the same name. `effect orders.load OrderKey -> Order ! StoreError = db.get("records")` with `type OrderKey { order_id: String }`. No new syntax.
- **B.** The key in the call: `db.get("records", order_id)`. New syntax in the transport call; the input TYPE is free.
- **Default: A**, because it keeps the DL-129 line form, follows Q5-1 B (a domain field is the key, not the host row id) and needs no parser change. Big: it fixes the meaning of a `db.get` input TYPE. Pinned by N7 and N12.
- → By: Opus (PLAN db-transport, default, open)

### QDB-2 · Migrate · big · The `BeamlDb` signatures

- **A.** Three functions of arity 3: `put(table, {type, version}, core)`, `get(table, type, key)`, `list(table, type, query)`; `{:ok, id}`, `{:ok, row | nil}`, `{:ok, [row]}` or `{:error, reason}`; `row = %{"id", "version", "value"}` with String keys.
- **B.** The 0005 plan text: `put(table, type, version, value)` (arity 4), the rest as in A.
- **Default: A**, because all three calls then carry `(table, what, payload)`, the version travels with the TYPE name it belongs to, and the payload is the ROW CORE (Q5-10 B), not a bare value. Big: a host-called name (DL-139). It changes the 0005 plan's put/4 line; the 0005 GREEN builds put/3. Pinned by N2 and N7.
- → By: Opus (PLAN db-transport, default, open)

### QDB-3 · Migrate · `db.get` with several rows of one key

- **A.** The newest row wins (`ORDER BY inserted_at DESC, id DESC LIMIT 1` in the host).
- **B.** Several rows are a failure `reason: "ambiguous"`; a unique index per TYPE and key keeps one row.
- **Default: A**, because `db.put` appends (no upsert in DL-129) and 0005 uses no `db.get` (P5-05). B needs an index per TYPE, a DDL that a TYPE change would touch (against DL-127). Pinned by the fake in N7 only.
- → By: Opus (PLAN db-transport, default, open)

### QDB-4 · Migrate · One row of a `db.list` fails its decode

- **A.** The whole call fails with the reason of the first failing row (`decode` or `constructor`). No row is skipped.
- **B.** The row is skipped; the span gets an attribute with the skipped count; the call succeeds.
- **Default: A**, because a skipped row is lost data with no trace at the page, and `--stored` already blocks the build for a failing decodable row (DL-102). B hides a corrupt row. Challenge: a bad-digest row passes `--stored` (counted, DL-136) and breaks the page. Pinned by N6.
- → By: Opus (PLAN db-transport, default, open)

### QDB-5 · Migrate · big · Where the db call records go and what they hold

- **A.** The outbound capture stream `"responses"`, one record per db call: the v3 core plus the extra `request`; `value` is the output projection (put: the written value; get: the row value; list: `{"items": [...]}`).
- **B.** A separate stream `"db"`; `value` holds row references (ids and digests), not values.
- **Default: A**, because one outbound stream with one format is DL-143, the REPLAY RUN needs the values (DL-129: replay as for any EFFECT), and P3 selects by operation in one list. B makes a REPLAY RUN read the live table. Big: record format and stream. Pinned by N10 and N11.
- → By: Opus (PLAN db-transport, default, open)

### QDB-6 · Migrate · big · The `outcome` and `reason` values of a db call record

- **A.** `outcome` `"ok"` with `reason: null`, or `"failed"` with `reason` one of `"transport"`, `"decode"`, `"constructor"`, `"not_found"`.
- **B.** The ENTRY RECORD words: `"accepted"` and `"rejected"`.
- **Default: A**, because "rejected" means a refused input at the entry (DL-133, DL-141); a db call does not refuse, it fails. Big: record format. If P2 names outbound outcomes, the P2 names win (PDB-01) and this question closes into the P2 one. Pinned by N10.
- → By: Opus (PLAN db-transport, default, open)

### QDB-7 · Migrate · big · The ROW SNAPSHOT file

- **A.** `rows.jsonl` beside the `--stored` file (the `entries.jsonl` pattern, R6D-04). Each line: the ROW CORE plus `"source": "db"` and `"row_id"`. `snapshot-meta.json` beside it; the compiler reads only its `row_count`.
- **B.** One mixed `--stored` file: RESPONSE RECORDS and rows in one JSONL, told apart by `source`.
- **Default: A**, because it follows the DL-134 build, keeps each stream's line count apart (M9 untouched) and lets the compiler see a missing ROW SNAPSHOT (PDB-23). Big: a record format that `mix beaml.stored` writes. Pinned by N17 to N24.
- → By: Opus (PLAN db-transport, default, open)

## Undo and Repair decisions

Format: **ID · class · decision.** Chose / Over / Because. Commits us to (Repair only).

**PDB-01 · Repair · Plan against the DL-143 core; the P2 key names win.**
Chose: the core keys of DL-143 with `version: 3`, `span_id`, `outcome`, `reason`. Over: wait for the P2 ledger. Because: no P2 ledger exists at this plan; P2 runs before P4 (0005 order). Commits us to: the P4 RED worker reads the P2 ledger and maps every key name before writing tests.
→ By: Opus (PLAN db-transport)

**PDB-02 · Repair · Two behaviour steps in one ledger: P4a transports, P4b `--stored` over rows.**
Over: one RED and one GREEN for all. Because: two code paths (generated Elixir vs compiler check); a smaller RED is easier to review. Commits us to: two RED reviews, one TEST and one review.
→ By: Opus (PLAN db-transport)

**PDB-03 · Undo · The KIND check names all four transports; a fifth name is an error with a help line.**
Chose: `unsupported effect kind: <k> in effect <op> (supported: http.post, db.put, db.get, db.list)` plus a help line. Because: the existing text says "slice 1 supports http.post", which is false after P4.
→ By: Opus (PLAN db-transport)

**PDB-04 · Undo · The table String must be `"records"`.**
Over: any lower-case name. Because: DL-127 has one table; a second table needs DDL, which BEAML does not own. Changes the S13 text of `bad/unsupported_effect_kind.beaml` (named in the plan table).
→ By: Opus (PLAN db-transport)

**PDB-05 · Repair · A ROW TYPE is a plain record: no own constructor, no redacted field, no LIST TYPE field.**
Over: any TYPE. Because: a constructor TYPE row would decode through `T.new`, a redacted field touches M3 (parked), a nested list has no decode. Commits us to: a ROW TYPE with these needs its own step.
→ By: Opus (PLAN db-transport)

**PDB-06 · Undo · The http.post wire rules (D6B-40, D6B-19, D6B-03) do not apply to db EFFECTS; db EFFECTS get their own check branch.**
Because: the ROW CORE holds a typed projection with an encode (PDB-13); the http limits exist for lack of a wire encode. http behaviour and texts do not change.
→ By: Opus (PLAN db-transport)

**PDB-07 · Undo · An enum in a ROW TYPE needs ENUM LITERALS and a keep-value variant.**
Over: tagged enums without literals. Because: the row stores an enum by its literal; a tagged enum has no JSON form (D6B-40 reason).
→ By: Opus (PLAN db-transport)

**PDB-08 · Repair · LIST TYPE `[T]` only as the one field of a `db.list` output TYPE (Q5-3 A, smallest form).**
Chose: lexer symbols `[` `]`, field TYPE text `[T]`, `__beaml_valid__(v, "[T]")` as `is_list` plus element check, emitted only when a LIST TYPE exists. Over: lists in every position. Because: `db.list` is the only producer; no list operation exists. Commits us to: a grammar rule and a fmt case (N15, N16).
→ By: Opus (PLAN db-transport)

**PDB-09 · Repair · D6B-39 is narrowed for ROW TYPES: a MIGRATE CHAIN may coexist with constructor and literal enum fields that no MIGRATE CHANGE names.**
Chose: the versioned decode runs the MIGRATE CHANGES on wire values, then the DL-101 tail (literal map, constructors, shape). Over: keep D6B-39 (0005 N7 then cannot build). Because: the 0005 v2 `Order` adds `note` and keeps `amount` and `channel`. Commits us to: per-version wire TYPE checks; a change that names such a field stays an error.
→ By: Opus (PLAN db-transport)

**PDB-10 · Undo · The 0004 harness gets a fake `BeamlDb` stub module, not an ExUnit suite.**
Over: ExUnit (as the task text says). Because: 0004 has no Mix project; every runtime test compiles stub modules from Python (`slice6_effect_reach_test.py`). The real Postgres stays in 0005.
→ By: Opus (PLAN db-transport)

**PDB-11 · Undo · `BeamlDb` returns rows with String keys at every level.**
Because: Postgrex returns `jsonb` decoded with String keys; the fake mimics it by a `:json` round trip.
→ By: Opus (PLAN db-transport)

**PDB-12 · Repair · Every non-`{:ok, _}` result, raise or exit of a `BeamlDb` call is `reason: "transport"`; the host reason is never read.**
Over: pass the host reason. Because: "transport, status and decode never raise to the caller" (the http rule); a host text could carry a value into a record. Commits us to: a `try` with `rescue` and `catch :exit` around each call.
→ By: Opus (PLAN db-transport)

**PDB-13 · Repair · A generated encode from typed value to wire per ROW TYPE.**
Chose: map keeps String keys; constructor struct → its fields under String keys; enum variant → its ENUM LITERAL; keep-value variant → its String. Over: encode from the original input bytes (not available after a fn step). Because: `db.put` receives a typed value from a flow. Commits us to: the round-trip rule (decode of the encode equals the value), pinned by N4.
→ By: Opus (PLAN db-transport)

**PDB-14 · Repair · The ROW CORE keys and their values.**
Chose: `version: 3, trace_id, span_id, artifact_id, operation, attempt: 1, type, value, value_sha256, redacted: [], unknown_keys: [], unknown_fields, outcome: "ok", reason: nil`. Over: a bare projection (Q5-10 A). Because: Q5-10 B (By: Fable, default, open) and DL-143. Commits us to: P2 names win (PDB-01); the record format is Q5-10's OWNER question, not a new one.
→ By: Opus (PLAN db-transport)

**PDB-15 · Repair · The row decode order: TYPE name, digest, TYPE VERSION, MIGRATE CHAIN, DL-101 tail.**
Because: DL-054 types a stored value by its own version before any step; the digest first means no step runs on a changed value. Every failure is `"decode"` except a failed constructor (`"constructor"`).
→ By: Opus (PLAN db-transport)

**PDB-16 · Undo · The core `type` key decides the TYPE VERSION on read; the `version` column is not read by generated code.**
Over: the column. Because: the core carries version and fingerprint (DL-043); the column serves the host query and index only. A column that disagrees with the core is a hand edit.
→ By: Opus (PLAN db-transport)

**PDB-17 · Undo · db call records carry the extra `request` (the input projection).**
Over: no request. Because: the http record has `request`; the REPLAY RUN and the record reader keep one shape (DL-143 extras).
→ By: Opus (PLAN db-transport)

**PDB-18 · Repair · `unknown_fields` of a `db.list` record uses dotted names with the item index (`items.0.channel`).**
Over: a union of field names. Because: DL-122 must tell "kept at capture" from "literal lost now" per item (DL-142 reason). Commits us to: the `--stored` check of list records reads indexed names (N25).
→ By: Opus (PLAN db-transport)

**PDB-19 · Repair · A REPLAY RUN never calls `BeamlDb`; it decodes the recorded `value`.**
Because: DL-129 says a db call replays as any EFFECT; a REPLAY RUN must not read the live table. Commits us to: N11 with the `:forbid` fake mode.
→ By: Opus (PLAN db-transport)

**PDB-20 · Undo · The `HTTP` module is emitted only when an `http.post` EFFECT exists.**
Because: a db-only source has no TCP transport. http sources keep their bytes (N13).
→ By: Opus (PLAN db-transport)

**PDB-21 · Undo · `mix beaml.stored` writes a new directory per build with `rows.jsonl`, `responses.jsonl` and `snapshot-meta.json`.**
Because: QDB-7 A and the 0005 N8c provenance check (P5-19). The task itself is 0005 host code.
→ By: Opus (PLAN db-transport)

**PDB-22 · Repair · The compiler checks `row_count` of `snapshot-meta.json` against the row lines.**
Over: ignore the meta file. Because: a partial ROW SNAPSHOT would pass with fewer rows (false pass). Commits us to: one more read; only `row_count` is read.
→ By: Opus (PLAN db-transport)

**PDB-23 · Repair · A source with `db.get` or `db.list` and no `rows.jsonl` fails the build.**
Over: no file means no rows (the `entries.jsonl` rule). Because: DL-094, "an unknown store is not an empty store"; rows are the main store of 0005. Commits us to: `db.put`-only sources need no ROW SNAPSHOT.
→ By: Opus (PLAN db-transport)

**PDB-24 · Undo · On success `--stored` prints one count line for rows: `rows: N rows, K checked, M not decodable`.**
Because: DL-136 and DL-138 give each stream a count line; never a value or id (DL-124).
→ By: Opus (PLAN db-transport)
