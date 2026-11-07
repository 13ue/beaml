# Plan: DB TRANSPORTS `db.put`, `db.get`, `db.list` and `--stored` over STORED ROWS (EXPERIMENT 0005 prerequisite P4)

**[Proposal]** PLAN phase, 2026-11-07. Task records only. No production file, no test, no commit, no `run.py` run.
Decisions: DL-127, DL-129, DL-137, DL-143, DL-144 (free run) in [the decision log](../../../../../wiki/planning/decision-log.md). Also read: DL-043, DL-054, DL-101, DL-102, DL-105, DL-122, DL-124, DL-134, DL-136, DL-138, DL-140 (literal swap), DL-141, DL-142; D036 (M3, M4, M5, M8, M9 parked); the 0005 [plan](../../../../0005-prototype-fullstack/workflow/2026-11-07/plan.md) and [decisions](../../../../0005-prototype-fullstack/workflow/2026-11-07/decisions.md) (Q5-1 to Q5-10, P5-18 to P5-25); the slice 6d [plan](../slice6d-inbound-effect/plan.md); `experiments/0001-syntax-to-beam/src/main.rs` at HEAD 35c7e3bf (read only: `effects()` line 1470, `emit_effect` line 3403, `emit_entry` line 3852, `check_stored` line 4685, `build_with_refusals` line 5280).
Design decisions and OWNER questions: [decisions.md](decisions.md) (PDB-01 to PDB-24, QDB-1 to QDB-7). Big ones: appended to the 0005 [owner-review.md](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md) under "Database transports (P4)".
By: Opus (PLAN db-transport) for every proposal in this file. Every Migrate question has a built default under DL-144: `By: Opus (PLAN db-transport, default, open)`.

Record format v3: no P2 ledger exists at this plan (`workflow/2026-11-07/record-format-v3/` is absent). This plan uses the DL-143 core only. **When P2 names a key differently, the P2 name wins** and this plan follows it without a new decision (PDB-01).

Proposed terms (glossary entry in the docs phase before GREEN prose uses them): DB TRANSPORT (one of `db.put`, `db.get`, `db.list`), STORED ROW (one row of `records`, DL-127), ROW CORE (the v3 record core in the `value` column, Q5-10 B), ROW SNAPSHOT (`rows.jsonl`, the file that `--stored` reads), ROW TYPE (the TYPE of the ROW CORE), LIST TYPE (`type OrderList { items: [Order] }`).

## Facts the step builds on (observed at HEAD 35c7e3bf)

- **[Verified]** `effect` lines parse `KIND("text")` with any dotted KIND (main.rs line 640). `effects()` rejects every KIND but `http.post`: `unsupported effect kind: <k> in effect <name> (slice 1 supports http.post)` (line 1476). `tests/slice6_pipe_test.py` S13 asserts this text for `bad/unsupported_effect_kind.beaml`, which uses `db.get("payments/authorize")`.
- **[Verified]** The http EFFECT rules are wire rules: no enum in an input (D6B-40), no constructor TYPE in an input or failure (D6B-19), no Int in an input (D6B-03), output fields String, literal enums or constructor TYPES; a constructor or enum field cannot stand in a TYPE with a MIGRATE CHAIN (D6B-39, lines 1590 to 1613).
- **[Verified]** The versioned decode `__beaml_decode_<t>(bytes, type_version)` picks the TYPE VERSION by `{version, fingerprint}`, types the body by that version (DL-054), runs the MIGRATE CHANGES and ends with `__beaml_valid__(shape, T)`. The literal map and the constructor tail run only in `plain_decode` (line 3783).
- **[Verified]** The lexer has no `[` or `]` token (`unsupported token at byte N`, line 102). TYPES are records, enums, `String`, `Int`.
- **[Verified]** `__beaml_valid__/2` is emitted per TYPE: a struct check for a constructor TYPE, a map check for a record TYPE (lines 2819 to 2860).
- **[Verified]** Replay helpers `body/1` and `digest/3` (D6B-58) check and re-encode a projection with `value`, `redacted`, `unknown_keys`, `value_sha256` (line 4270).
- **[Verified]** `--stored S` reads S as RESPONSE RECORDS version 2 and `entries.jsonl` beside S (DL-134, R6D-04, line 5317). A source with an EFFECT needs `--stored` (line 5341). DL-136 (skip non-replayable records, count line) is not built for RESPONSE RECORDS; `check_entries` prints `N entries, K checked, M rejected at capture`.
- **[Verified]** 0004 has no ExUnit project. Runtime tests compile the generated module with Elixir stub modules (`ProbeSupport`, `Capture`, `:otel_span`) from Python (`slice6_effect_reach_test.py` `STUBS`).
- **[Verified]** 0005 scaffold: `records(id identity, type text, version integer, value jsonb, inserted_at)` with index `(type, inserted_at)` (`app/priv/repo/migrations/20261107000000_create_records.exs`). No `BeamlDb`, no `mix beaml.stored` yet.

## Preconditions

- **P2** (record format v3), **P3** (several ENTRY LINES and EFFECTS per source, `Replay` selects by operation), **P5** (module name from the file stem, `defmodule Orders`) are GREEN and TESTED. 0005 order: P1 → P2 → P3 → P5 → P4.
- **[Inference]** Without P3 the fixture (three db EFFECTS) stops at `slice 1 supports one effect`. That text is a missing precondition, never this step's RED.

## Split (PDB-02)

One ledger, two behaviour steps, each with its own RED, RED review and GREEN:
- **P4a, transports.** Parse and check, LIST TYPE, generated calls, ROW CORE write, row decode through the MIGRATE CHAIN, db call records, REPLAY RUN. Tests N1 to N16.
- **P4b, `--stored` over rows.** ROW SNAPSHOT `rows.jsonl`, DL-102 / DL-122 / DL-140 / DL-136 / DL-124 over rows and over db call records. Tests N17 to N27.
- Reason: two concerns with separate code paths (generated Elixir vs the compiler check). P4b needs the ROW CORE of P4a as its input.

## Syntax (no new line form)

```
effect orders.save Order -> Order ! StoreError = db.put("records")
effect orders.load OrderKey -> Order ! StoreError = db.get("records")
effect orders.list OrderQuery -> OrderList ! StoreError = db.list("records")
type OrderList { items: [Order] }
```

- The three KINDS are ordinary `effect` targets (DL-129). The String is the table; only `"records"` is valid (DL-127, PDB-04).
- **LIST TYPE (Q5-3 A, PDB-08).** A field TYPE `[T]`. New lexer symbols `[` and `]`; the field TYPE text is `[Order]` (also in the fingerprint). Allowed only as the one field of the output TYPE of a `db.list` EFFECT, with `T` a ROW TYPE. No list literal, no list pattern, no list operation.
- **`db.get` key (QDB-1, default A).** The input TYPE has exactly one String field; its name is the key; the ROW TYPE has a String field of that name. No new syntax. Q5-1 B (a TYPE field names the key) holds; the field is named by the key TYPE, not by a call argument.

## Checks (PDB-03 to PDB-10)

Order of checks per db EFFECT, so each text is reachable: KIND, table, name and duplicate (shared), failure TYPE with `reason: String` (shared), transport shape, ROW TYPE rules.

| Check | Text (exact; `<op>` the EFFECT name) |
|---|---|
| fourth KIND | `unsupported effect kind: <k> in effect <op> (supported: http.post, db.put, db.get, db.list)` + newline + `  help: write http.post("path"), db.put("records"), db.get("records") or db.list("records")` |
| table | `error: effect <op>: <k> uses the table "records" only (DL-127)` |
| put head | `error: effect <op>: db.put returns its input TYPE; write <In> -> <In>` |
| get key | `error: effect <op>: db.get takes a key TYPE with one String field (QDB-1)` |
| get key field | `error: effect <op>: the key field <f> of <In> is not a String field of <Out> (QDB-1)` |
| list query | `error: effect <op>: db.list takes a query TYPE with no fields (Q5-2)` |
| list output | `error: effect <op>: db.list returns a TYPE with one field of a LIST TYPE, for example type OrderList { items: [Order] } (Q5-3)` |
| list elsewhere | `error: the LIST TYPE [<T>] of <Owner>.<f> stands only as the field of a db.list output TYPE (Q5-3)` |
| list element | `error: the LIST TYPE [<T>] needs a record TYPE inside the brackets` |
| ROW TYPE own constructor | `error: effect <op>: the ROW TYPE <R> has a constructor; a row holds a plain record (PDB-06)` |
| ROW TYPE redacted | `error: effect <op>: the ROW TYPE <R> has the redacted field <f>; rows hold no redacted field yet (M3, DL-116)` |
| ROW TYPE enum without keep variant | `error: effect <op>: the enum <E> of <R>.<f> has no keep-value variant (DL-065)` + `  help: add the variant Unknown(String) to enum <E>` (the existing text form) |
| ROW TYPE enum without literals | `error: effect <op>: the enum <E> of <R>.<f> has no ENUM LITERALS; a row stores an enum by its literal (PDB-07)` |
| MIGRATE CHANGE on a constructor or enum field | `error: migrate <R>: the change of field <f> names a constructor or enum field; slice 6b has no MIGRATE STEP form for it (D6B-39)` |

- **ROW TYPE** (PDB-05): the input of `db.put`, the output of `db.get`, the element of the `db.list` output. A record TYPE, no own constructor, no redacted field, no LIST TYPE field. Fields: `String`, `Int`, constructor TYPES (S4 rule), literal enums with a keep-value variant, nested plain records.
- **D6B-39 narrowed (PDB-09).** A ROW TYPE with a MIGRATE CHAIN may hold constructor and literal enum fields when no MIGRATE CHANGE names them. Needed by the 0005 N7 (`add note`). The http output keeps the old rule (no byte or text change there).
- **Not changed:** the http.post rules. D6B-40, D6B-19 and D6B-03 stay for `http.post`. A db EFFECT does not go through them.

## Host module (Q5-8 A, QDB-2 default A)

The generated code calls one fixed module. `BeamlDb` exists in the host, never in generated code.

| Call | Receives | Returns |
|---|---|---|
| `BeamlDb.put(table, {type, version}, core)` | `"records"`; `{"Order", 1}`; the ROW CORE map (atom keys, as `Capture.write` records) | `{:ok, id}` (integer) or `{:error, reason}` |
| `BeamlDb.get(table, type, key)` | `"records"`; `"Order"`; `%{"order_id" => "order-1"}` (the key projection) | `{:ok, row}`, `{:ok, nil}` or `{:error, reason}` |
| `BeamlDb.list(table, type, query)` | `"records"`; `"Order"`; `%{}` (the query projection) | `{:ok, [row]}` or `{:error, reason}` |

- `row = %{"id" => integer, "version" => integer, "value" => core}` with String keys at every level, as Postgrex returns a `jsonb` value (PDB-11).
- **Order and limit** are the host's (Q5-2 A): `ORDER BY inserted_at DESC, id DESC LIMIT 100`. Generated code keeps the host order.
- **`get`** looks up `value->'value'->>'<key>' = $1` for `type = $2`, newest first, limit 1. Several rows with one key: the newest wins (QDB-3, default A).
- **Host reason:** never read. Every `{:error, _}`, every other return shape, every raise and every exit from a `BeamlDb` call is the failure `reason: "transport"` (PDB-12).
- **Signature change against the 0005 plan:** the 0005 plan text has `put(table, type, version, value)` (put/4). This step builds put/3 with `{type, version}` (QDB-2). Big: a host-called name.

## Generated code per transport (sketch; GREEN chooses the exact lines)

Common: `def orders_save(a0)`, `orders_load(a0)`, `orders_list(a0)` (name rule as for http, `.` → `_`); `__beaml_valid__(a0, In)` first, `invalid BEAML input` raise as for http; `__beaml_attempt__`; `ProbeSupport.span("<service>.<op>", :client, <input projection>, nil, fn -> ... end)`; a failure raises inside the span (outcome `error`, attribute `reason`) and returns `{:error, %Orders.StoreError{reason: r}}` outside it.

```elixir
# db.put
value = __beaml_encode_order(a0)                         # typed value -> wire map (PDB-13)
core = Replay.row_core("orders.save", value, __beaml_unknown_fields_order(a0))
case __beaml_db__(fn -> BeamlDb.put("records", {"Order", 1}, core) end) do
  {:ok, id} when is_integer(id) -> Replay.db_record(core, request); {:ok, a0}
  _ -> Replay.db_failed("orders.save", request, "transport"); __beaml_fail_orders_save("transport")
end
# db.get
case __beaml_db__(fn -> BeamlDb.get("records", "Order", key) end) do
  {:ok, nil} -> fail "not_found"
  {:ok, %{"value" => core}} -> case __beaml_row_order(core) do {:ok, v} -> record, {:ok, v}; {:error, r} -> fail r end
  _ -> fail "transport"
end
# db.list
case __beaml_db__(fn -> BeamlDb.list("records", "Order", %{}) end) do
  {:ok, rows} when is_list(rows) -> decode every row in order; all ok -> {:ok, %{"items" => items}}; first error r -> fail r
  _ -> fail "transport"
end
```

- **Encode (PDB-13).** `__beaml_encode_<t>/1` per ROW TYPE and per field TYPE it holds: a record map keeps its String keys; a constructor struct gives a map of its fields under String keys; a literal enum `{"Channel", "Web", []}` gives its ENUM LITERAL `"web"`; the keep-value variant `{"Channel", "Unknown", ["tv"]}` gives `"tv"`. Rule: the decode of the encoded bytes gives an equal value (N4).
- **ROW CORE (Q5-10 B, DL-143 core, PDB-14).** `%{version: 3, trace_id, span_id, artifact_id, operation: "orders.save", attempt: 1, type: %{name, version, fields, fingerprint}, value, value_sha256: digest(value, [], []), redacted: [], unknown_keys: [], unknown_fields, outcome: "ok", reason: nil}`. `type` is the newest TYPE VERSION of the ROW TYPE (fields in source order, fingerprint sorted, as the ENTRY RECORD `type`). `unknown_fields` lists the fields held as `Unknown(...)`, sorted. A row is written only on success, so `outcome` is always `"ok"` in a row.
- **Row decode `__beaml_row_<t>(core)` (PDB-15).** (1) `core["type"]["name"]` equals the ROW TYPE, else `"decode"`; (2) `body/1` (D6B-58 digest), else `"decode"`; (3) the versioned decode with `core["type"]` picks the TYPE VERSION by `{version, fingerprint}` (DL-043), types the stored value by that version (DL-054, wire TYPES), runs the MIGRATE CHANGES to the newest version (DL-127 lazy, on read); an unknown version or fingerprint is `"decode"`; (4) the DL-101 tail on the migrated wire map: literal map, constructors (`"constructor"` on a failed constructor, the outbound reason), shape check. The `version` column is not read; the core `type` decides (PDB-16).
- **Versioned decode with constructor and enum fields (PDB-09).** Today the versioned decode ends with `__beaml_valid__` and has no literal map or constructor tail. GREEN joins them: versioned wire read → MIGRATE CHANGES → the `plain_decode` tail. The per-version check uses wire TYPES: `String` binary, `Int` integer, literal enum binary, constructor TYPE a map whose signature keys hold Strings, record TYPE recursive.
- **List decode.** Every row in host order; the first failing row fails the whole call with its reason (QDB-4, default A). No row is skipped.
- **db call record (Q5-7 A, PDB-17, QDB-5 default A).** Every db call writes one record to the capture stream `"responses"` (the one outbound stream; P3 selects by operation): the v3 core plus the extra `request` (the input projection: the written value for put, the key for get, `%{}` for list). `value`: the output projection: the ROW CORE `value` for put, the decoded row's wire value for get, `%{"items" => [wire values]}` for list. `unknown_fields` of a list record: dotted names with the item index, `items.0.channel` (PDB-18). On a failure: `value: null`, `outcome: "failed"`, `reason` one of `"transport"`, `"decode"`, `"constructor"`, `"not_found"`.
- **REPLAY RUN (PDB-19).** In `Replay.run/3` a db step reads its record (P3 select by `trace_id` and `operation`), checks `body/1`, decodes `value` as the output TYPE (list: each item as the ROW TYPE at its newest version) and never calls `BeamlDb`. A recorded `outcome: "failed"` replays to the same failure reason.
- **No `HTTP` module** in a source without an `http.post` EFFECT (PDB-20). Bytes of http sources do not change (N13).

## Outcome per DL-136 (no `status` for db)

- `status` has no meaning for a db call (no HTTP). The core keys `outcome` and `reason` replace it (DL-141 form, DL-143 core).
- **Replayable db record:** `outcome: "ok"` and the digest holds. `--stored` checks only these; `outcome: "failed"` and bad-digest records are counted, not checked (DL-136 rule copied, DL-134 "every stream copies this answer").
- **Decodable row:** the core `type.name` is a ROW TYPE of a `db.get` or `db.list` EFFECT of the source, the digest holds and the TYPE VERSION is on the chain (DL-137: only rows that `db.get` or `db.list` would decode are checked). Every other row is counted, not checked.
- Names: QDB-6 (default A: `"ok"` / `"failed"`). Big: record format. If P2 names outbound outcomes differently, P2 wins.

## `--stored` over rows (P4b, Q5-4 B)

- **ROW SNAPSHOT (PDB-21, QDB-7 default A).** `rows.jsonl` beside the `--stored` file, as `entries.jsonl` (DL-134, R6D-04). One line per row: the ROW CORE plus two extras, `"source": "db"` and `"row_id": <id>`. `mix beaml.stored` (0005 host task, built in the 0005 GREEN) writes `rows.jsonl`, an empty `responses.jsonl` when no capture is passed, and `snapshot-meta.json` into a new directory per build, then runs `beaml-spike SOURCE --stored <dir>/responses.jsonl`.
- **`snapshot-meta.json`** (P5-19, 0005 plan repair): `{"table": "records", "database": "<name>", "query_time": "<UTC from SELECT now()>", "row_count": N, "row_ids": [sorted ids]}`. No row value. The compiler reads only `row_count`: when the file exists and `row_count` differs from the number of row lines, the build fails (PDB-22): `error: rows.jsonl holds <n> rows but snapshot-meta.json counts <m>; the ROW SNAPSHOT is partial`.
- **No ROW SNAPSHOT (PDB-23).** A source with a `db.get` or `db.list` EFFECT and no `rows.jsonl` beside `--stored` fails: `error: stored ROWS unknown: a source with db.get or db.list needs rows.jsonl beside --stored (an unknown store is not an empty store)`. A source with `db.put` only needs no ROW SNAPSHOT.
- **Line checks.** Not JSON: `error: stored ROW is not JSON`; no `"source": "db"`: `error: stored ROW has no source "db"`; core `version` other than 3: `error: stored ROW has record version <v>; this build reads record version 3 only (DL-143)`. Each with `  record source: <file>:<n> (line <n>)`.
- **Checks over decodable rows** (DL-102, DL-122, DL-140, DL-124, DL-137): the path check (the stored TYPE VERSION must exist on the chain of the ROW TYPE, the `no_path` text with the word ROW), the constructors (DL-102, through the step 13 Elixir run), the literals (DL-122 lost literal; DL-140 literal swap when P2 or its own step gives the stored variant; else out of scope, see Limits), the kept values (`unknown_fields`, DL-103 note). Per-row texts follow the RESPONSE RECORD texts with `stored ROW` for `stored RESPONSE RECORD` and `of table records` for `of operation <op>`:
  - constructor: `error: TYPE Order: 1 stored ROW of table records fails the constructor of Amount for field amount with BadAmount` / `  record source: <rows>:1 (line 1)` / `  help: declare the fate of these rows in a MIGRATE STEP to a new TYPE VERSION of Order (DL-102, DL-137)`.
  - lost literal: `error: TYPE Order v1: 1 stored ROW of table records holds a value of field channel that is no ENUM LITERAL of Channel now (DL-122)` / the record source line(s) / `  help: declare the fate in a MIGRATE STEP (DL-122); slice 6b has no MIGRATE STEP form for an enum field (D6B-39), so restore the removed or changed ENUM LITERAL of Channel`.
- **Count line (PDB-24).** On success, stderr gets one line: `rows: <n> rows, <k> checked, <m> not decodable`. Never a value, never a row id.
- **DL-124 text rule.** No message prints a stored value, a row id or `trace_id`. Line references only.
- **db call records in `responses.jsonl`.** Replayable `orders.save` and `orders.load` records: the existing per-record checks with the output TYPE (the ROW TYPE). `orders.list` records: each `value.items[i]` checked as the ROW TYPE, kept values by `items.<i>.<field>`. `outcome: "failed"` records: counted, not checked. Texts: the RESPONSE RECORD texts unchanged.
- **Parked items.** M4: no assertion on the help line beyond the text above being stable for this step; M9: no line-count assertion; M5: no `retire` for rows; M3: no redacted ROW field (checked out); M8: generated code takes no failure struct as input.

## Fixtures (`experiments/0004-generated-replay/slice6/db/`)

- `orders.beaml`: the 0005 domain types (`BadAmount`, `Amount` with the `_, ""` clause, `Channel { Web = "web"  App = "app"  Unknown(String) }`, `Order`, `OrderKey { order_id: String }`, `OrderQuery {}`, `OrderList { items: [Order] }`, `StoreError`), the three db EFFECTS above, and `fn save o: Order -> Order ! StoreError = o |> orders.save`, `fn load k: OrderKey -> Order ! StoreError = k |> orders.load`, `fn list_orders q: OrderQuery -> OrderList ! StoreError = q |> orders.list`.
- `order_v2.beaml`: `orders.beaml` with `type Order v2 { ... note: String }` and `migrate Order v1 -> v2 { add note: String = "" }`.
- `stricter.beaml`: `orders.beaml` with `fn Amount "0", _ -> Amount ! BadAmount = BadAmount {}` before the general clause.
- `no_app.beaml`: `orders.beaml` without `App = "app"`.
- `put_only.beaml`: `Order`, `StoreError`, `orders.save` and `save` only (PDB-23 control).
- `stored/responses.jsonl` (empty), `stored/rows.jsonl` (empty); per-test row files are written by the test into a temp directory (ROW CORES built by the test with its own digest and fingerprint code, never by the compiler).
- `bad/*.beaml`: one file per N12 text.
- Values: `order1 = %{"order_id" => "order-1", "amount" => %Orders.Amount{value: "12.50", currency: "EUR"}, "channel" => {"Channel", "Web", []}}`, `wire1 = {"order_id":"order-1","amount":{"value":"12.50","currency":"EUR"},"channel":"web"}`; `order2` same with `order-2`; `tv` with `{"Channel", "Unknown", ["tv"]}` and wire `"tv"`.

## Host test harness (PDB-10)

- The step 12 runtime harness (`slice6_effect_reach_test.py` stubs: span stack, `Capture.write/2` appends `{kind, record}`, `:otel_span` attributes), plus a fake `BeamlDb` Elixir module in the same stub string. Not ExUnit: 0004 has no Mix project; the stub style is the 0004 pattern.
- Fake `BeamlDb`: an `Agent` or the process dictionary holds rows `%{"id", "type", "version", "value"}`. `put` stores `:json.decode(:json.encode(core))` (String keys, as `jsonb`), returns `{:ok, next_id}`. `list` returns rows of the type, `id` descending. `get` returns the newest row whose `value.value[key field]` equals the key value, or `nil`. Every call is logged `{:db, fun, table, type_or_head, arg_keys}`. Modes in `:persistent_term`: `:ok`, `:down` (`{:error, "down"}`), `:raise` (raises), `:exit` (`exit(:noproc)`), `:junk` (returns `:what`), `:forbid` (raises and logs: used by N11 to prove no call).
- The real Postgres and the real `BeamlDb` (Ecto `SQL.query/3`) are 0005 only. P4 changes no 0005 file.

## First failing test: `tests/slice6_db_test.py`

Expected values come from this plan, DL-127, DL-129, DL-143 and the test's own digest and fingerprint code, never from the new compiler. Run: `python3 -B experiments/0004-generated-replay/tests/slice6_db_test.py [-k NAME]`.

**P4a**

- **N1 (first RED).** `orders.beaml --stored stored/responses.jsonl` exits 0; stdout has `def orders_save(`, `def orders_load(`, `def orders_list(`. Today: exit 1 with `unsupported token at byte <n>` (the `[` of `[Order]`) or `unsupported effect kind: db.put ...`. Both are this step's missing behaviour. A P3 text (`slice 1 supports one effect`) or a missing module is not RED.
- **N2 (put writes the ROW CORE).** `Orders.save(order1) == {:ok, order1}`. The fake got one put: `"records"`, `{"Order", 1}`. The stored core has exactly the PDB-14 keys; `value == wire1`; `value_sha256` equals the test's D6B-58 digest of `wire1`; `type` equals `%{"name" => "Order", "version" => 1, "fields" => [["order_id","String"],["amount","Amount"],["channel","Channel"]], "fingerprint" => <test sha256>}`; `outcome == "ok"`, `reason == nil`, `unknown_fields == []`, `unknown_keys == []`, `redacted == []`.
- **N3 (kept value).** `save(tv)` stores `channel: "tv"` and `unknown_fields == ["channel"]`.
- **N4 (list round trip).** `save(order1)`, `save(order2)`, `save(tv)` then `Orders.list_orders(%{}) == {:ok, %{"items" => [tv, order2, order1]}}` (fake order). `Unknown("tv")` comes back as `{"Channel", "Unknown", ["tv"]}`.
- **N5 (MIGRATE CHAIN on read).** Under `order_v2.beaml`: the fake holds one v1 ROW CORE built by the test (v1 fingerprint, v1 digest). `list_orders(%{})` gives the item with `"note" => ""`. The fake row still has `version` 1 and the same core (lazy). Then `save(order3_v2)` writes `{"Order", 2}` with `value.note == ""`; the list holds the v2 row and the v1 row.
- **N6 (row decode rejects).** Each fake core gives `{:error, %Orders.StoreError{reason: R}}` from `list_orders` and from `load`: changed `value` (digest) `"decode"`; `type.name` `"Payment"` `"decode"`; `type.version` 7 `"decode"`; changed fingerprint `"decode"`; `value.amount.currency` `""` with a matching digest `"constructor"`; a non-map core `"decode"`.
- **N7 (get).** After `save(order1)`: `Orders.load(%{"order_id" => "order-1"}) == {:ok, order1}`; the fake got key `%{"order_id" => "order-1"}` and type `"Order"`. `load(%{"order_id" => "none"}) == {:error, %Orders.StoreError{reason: "not_found"}}`.
- **N8 (transport never raises).** For each fake mode `:down`, `:raise`, `:exit`, `:junk`: `save`, `load` and `list_orders` each return `{:error, %Orders.StoreError{reason: "transport"}}`; the process lives; no row is added.
- **N9 (spans).** `save(order1)` logs `{:span, "orders.orders.save", "order-1", nil}` with kind `:client`; `list_orders(%{})` logs `{:span, "orders.orders.list", nil, nil}`; a failure sets the attribute `reason`.
- **N10 (db call records).** After `save(order1)`: one `"responses"` record, keys = PDB-14 keys + `request`, `operation: "orders.save"`, `value == wire1`, `value_sha256` equal to the row's. After `list_orders` over `tv` and `order1`: `value == {"items": [<tv wire>, wire1]}`, `unknown_fields == ["items.0.channel"]`. After a `:down` save: `outcome: "failed"`, `reason: "transport"`, `value: null`.
- **N11 (REPLAY RUN).** The records of N10 through `:json` encode and decode; fake mode `:forbid`. `Orders.Replay.run(order1, trace_id, records)` (flow `save`) and the list flow return the live results; the fake log has no call. A `"failed"` record replays to `{:error, %Orders.StoreError{reason: "transport"}}`.
- **N12 (compile rejects).** One `bad/` file per row of the Checks table; each exits non-zero with its exact text.
- **N13 (byte guard, passes before and after).** The four pin sites stay equal: `tests/slice5_syntax_test.py` PIN, `tests/slice6_pipe_test.py` `EFFECT_OUTPUTS`, `tests/slice6_host_struct_test.py` `BYTE_GUARD`, `slice6/effect-reach/byte-guard.json`; `payments.generated.snapshot` equal. Every tracked source without a db EFFECT or a LIST TYPE compiles byte-equal against the P4 base commit (`git archive` build).
- **N14 (events).** Every compile keeps the harness check: no source text, no path in `.beaml/actions.jsonl`.
- **N15 (fmt).** `beaml-spike fmt` on every `slice6/db/*.beaml` changes nothing; `[Order]` keeps its bytes.
- **N16 (grammar).** `integrations/zed-beaml`: `_field_type` accepts `list_type: seq("[", $.type, "]")`; a corpus case `test/corpus/list_type.txt`; a highlight line (`[`, `]` punctuation, `Order` type). `tree-sitter generate`, `tree-sitter test --rebuild`, `tree-sitter test --wasm --rebuild` pass.

**P4b** (row files written by the test into a temp directory beside an empty `responses.jsonl`)

- **N17 (clean rows).** `orders.beaml` with two decodable v1 rows: exit 0; stderr has `rows: 2 rows, 2 checked, 0 not decodable`.
- **N18 (stricter constructor blocks).** `stricter.beaml` with a row `amount.value "0"`: exit 1; stderr has the constructor text above (line 1); stderr contains neither `order-zero` nor `"0"`. Control: the same rows with `orders.beaml` exit 0. Data control: the row removed, `stricter.beaml` exit 0.
- **N19 (lost literal).** `no_app.beaml` with a row `channel "app"`: exit 1, the DL-122 row text. A row `channel "tv"` with `unknown_fields ["channel"]`: exit 0.
- **N20 (chain).** A v1 row under `order_v2.beaml`: exit 0. A row with a fingerprint on no chain version: exit 1, the path text with `stored ROW` and `Order`.
- **N21 (not decodable, counted).** A row with a bad digest, a row with `type.name "Invoice"`: exit 0; `rows: 3 rows, 1 checked, 2 not decodable`.
- **N22 (unknown store).** `orders.beaml` with no `rows.jsonl` beside: exit 1 with the PDB-23 text. `put_only.beaml` with no `rows.jsonl`: exit 0.
- **N23 (line form).** A row without `source`; a row with core `version` 2; a non-JSON line: each its text and line.
- **N24 (meta).** `snapshot-meta.json` with `row_count` 3 beside two rows: exit 1 with the PDB-22 text; `row_count` 2: exit 0; no meta: exit 0.
- **N25 (db call records).** `responses.jsonl` with an `orders.list` record whose item 0 has `amount.value "0"` under `stricter.beaml`: exit 1 with the RESPONSE RECORD constructor text for `orders.list`; the same record with `outcome: "failed"` and `value: null`: exit 0.
- **N26 (DL-124).** Across N18 to N25: stderr never holds a stored String, a row id or a `trace_id` of the fixtures (the test lists the values it wrote and asserts each is absent).
- **N27 (events).** N14 for every P4b compile.

## Existing assertions that change (each by name)

| File | Assertion | Today | After P4 |
|---|---|---|---|
| `tests/slice6_pipe_test.py` | `BAD["unsupported_effect_kind.beaml"]` (S13) | `unsupported effect kind: db.get in effect payments.authorize (slice 1 supports http.post)` | `error: effect payments.authorize: db.get uses the table "records" only (DL-127)`. The fixture stays; `db.get` is now a KIND, the table check fires first. |

- **[Inference]** No other test asserts the old KIND text (grep over `tests/`, `0001/tests/cli.rs`). The new fourth-KIND text is asserted by N12. A worker re-greps at RED.
- **[Inference]** No test asserts `unsupported token` for `[` (grep: `slice6_int_test.py` uses `-`, `slice4_retire_test.py` and `slice5_syntax_test.py` use `-` and `.`).

## Byte changes

- **None** for any existing source (N13). The http emit (`emit_effect`, `HTTP`, `Replay.record/3`) is not touched for `http.post`. GREEN may move shared parts (decode tail, `__beaml_attempt__`, `BeamlFailure`) for reuse; N13 proves the move keeps bytes.
- **New:** outputs of the `slice6/db/` fixtures and the N12 inline sources.
- **Re-pin rule:** if a GREEN finds it must change any existing byte, it stops and reports a blocker. A re-pin moves all four sites together with a diff proof (byte pin memory note).

## Checks

- 0001: `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings`. New unit tests `db_transport_kinds` (parse and checks) and `list_type_field`.
- 0004: `tests/slice6_db_test.py`, every `slice6_*_test.py`, `slice5_syntax_test.py`, the compile-level test files; `python3 -B experiments/0004-generated-replay/run.py` once at the TEST phase.
- `integrations/zed-beaml`: `tree-sitter generate`, `tree-sitter test --rebuild`, `tree-sitter test --wasm --rebuild`.

## Order

- After P2, P3 and P5 are GREEN and TESTED. One code-writing worker at a time (`main.rs`). P4a RED → RED review → GREEN, then P4b RED → RED review → GREEN, then one TEST and one review for both.
- 0005 then builds `BeamlDb` (Ecto `SQL.query/3`) and `mix beaml.stored` to the contracts above, and runs its N2 to N8c against Postgres.

## Exclusions

- `db.query` or SQL text (DL-129 option S). A filter field in the query TYPE (Q5-2 B). Pagination or a cursor.
- A LIST TYPE anywhere but the one field of a `db.list` output; generics; list literals, patterns, operations; a list of String or Int.
- A ROW TYPE with its own constructor, a redacted field (M3), or a LIST TYPE field. A MIGRATE CHANGE on a constructor or enum field of a ROW TYPE (D6B-39 kept).
- An eager rewrite of old rows. Rows stay at their version (DL-127 lazy read).
- Fate forms for rows (`quarantine`, `retire`, `map`, DL-125, DL-137): the fate slice P6, blocked by D036.
- A DL-136 count line for RESPONSE RECORDS (its own RED TEAM step). P4 skips failed db call records without a line in `responses.jsonl`.
- The real Postgres, `BeamlDb`, `mix beaml.stored` and `snapshot-meta.json` writing: EXPERIMENT 0005.
- `with` (redacted wire fields) on a db EFFECT: an error (no redacted ROW field).

## Limits

- **[Inference]** One corrupt row fails the whole `db.list` (QDB-4 A), while `--stored` only counts it (DL-136). The build is green and the page fails loudly. The same split holds for RESPONSE RECORDS today.
- **[Unknown]** Whether `jsonb` keeps every value that `:json.encode` writes so that the D6B-58 digest holds on read (float text, very large integers). ROW TYPES hold Strings and Int only in 0005; the 0005 N2 digest check is the evidence.
- **[Unknown]** Whether the joined versioned decode and DL-101 tail fit the current `decode_parts` without byte change for http outputs. N13 decides; the RED worker probes once and records it.
- **[Inference]** DL-140 (literal swap) needs the stored variant. A ROW CORE holds the wire literal, not the variant. If P2 adds no stored variant, a swap on rows is not seen; the limit is the same as for RESPONSE RECORDS until the DL-140 slice.
- **[Inference]** `row_id` in the ROW SNAPSHOT is a host key, not a stored value. It is used only by the 0005 N8c provenance check, never printed.
- **[Inference]** The fake `BeamlDb` mimics `jsonb` by a `:json` round trip only. Key order, duplicate keys and number forms of Postgres are 0005 evidence.
- **[Unknown]** The cost of `--stored` over all rows (one full read per build). Fine for a PROTOTYPE.
- **[Inference]** The host renders a `Channel` value from the tuple form. A literal helper for the host is not in P4.

## Plan repair (after plan check), 2026-11-07

**[Proposal]** PLAN repair after the [plan check](plan-review.md) BLOCK (O1 high, O2 high, O3 high; M-a, M-b medium). Main-agent rulings under DL-144 applied as given. This section overrides the sections above where they differ.
By: Fable (main agent, rulings under DL-144) for O1, O2 and O3; Opus (PLAN repair P3/P4) for the details marked so in [decisions.md](decisions.md#plan-repair-after-plan-check-2026-11-07).

### O1: the P2, P3 and P5 names

**Outcome words (P2).** QDB-6 is withdrawn. Every db record and every ROW CORE uses the v3 words. → By: Fable · Repair

| Fact | `outcome` | `reason` | `value` |
|---|---|---|---|
| Call succeeds; every ROW CORE | `"accepted"` | `:null` (JSON `null`) | the output projection |
| `BeamlDb` error, other shape, raise, exit | `"rejected"` | `"transport"` | `:null` |
| Row decode fails (name, digest, version, fingerprint, not JSON) | `"rejected"` | `"decode"` | `:null` |
| Row constructor fails | `"rejected"` | `"constructor"` | `:null` |
| `db.get` finds no row | `"rejected"` | `"not_found"` | `:null` |

- New big open question **QDB-6b**: a failed db call is a rejected record with its reason. Challenge: the v3 http writer writes no record on a transport failure; a db call writes one. → By: Fable (default, open) · Migrate
- PDB-14: `outcome: "accepted"`, `reason: :null`. Changes N2, N10, N11, N25 and the owner-review QDB-6 line.
- `--stored` over `responses.jsonl`: db records follow QV3-8 B. A `rejected` db record skips the value checks, the TYPE path check and the W2 count. It counts in the P2 count lines `N records, K checked, M rejected at capture` and `digest not verified (P2b)`. → By: Opus (PLAN repair P3/P4) · Undo
- The exclusion "A DL-136 count line for RESPONSE RECORDS ... P4 skips failed db call records without a line" is withdrawn: P2 builds the count line.
- `rows.jsonl`: a row with `outcome` other than `"accepted"` is counted as not decodable, not checked (a row is written on success only, so such a row is a hand edit). → By: Opus (PLAN repair P3/P4) · Undo

**Module (P5, Q6E-1 C).** The fixture gets an ENTRY LINE, so its module is `Orders`: → By: Fable · Repair

```
effect ui.orders OrderQuery -> OrderList ! StoreError = ui.event("orders") |> list_orders
```

- It is the 0005 entry form. **[Unknown]** whether an ENTRY LINE with the empty input TYPE `OrderQuery {}` passes the P1 checks; the RED worker probes it once and records it. It is 0005 evidence too.
- Variants in their own directories, each as `orders.beaml` (P3 O1 ruling): `slice6/db/plain/`, `plain_v2/`, `order_v2/` (now a reject case, see O3), `stricter/`, `no_app/`, `put_only/`. Each runtime variant keeps the ENTRY LINE. `put_only/` is a compile-only case (N22) and needs none. → By: Opus (PLAN repair P3/P4) · Undo

**Replay (P3, Q6E-3 A).** The fixture has three EFFECTS, so the call is `Orders.Replay.run(operation, a0, trace_id, records)`. `select/2` stays by `trace_id` only (one EFFECT per flow, Q6E-4 A). The words "P3 select by `trace_id` and `operation`" in PDB-19 and "P3 selects by operation in one list" in QDB-5 are withdrawn. → By: Fable · Repair

- **N11 (changed).** `Orders.Replay.run("orders.save", order1, trace_id, records)` and `run("orders.list", %{}, trace_id, records)` return the live results; the fake log has no call. A `rejected`/`transport` record replays to `{:error, %Orders.StoreError{reason: "transport"}}`. `run("orders.load", order1, save_trace, records) == {:error, :operation_mismatch}`.

### O2: one encoder (JSON binary at the `BeamlDb` boundary)

→ By: Fable · Repair, because it closes the `:null`/`nil` gap with one rule.

| Call | Receives | Returns |
|---|---|---|
| `BeamlDb.put(table, {type, version}, json)` | `"records"`; `{"Order", 1}`; `json` = `:json.encode(core)`, a binary, encoded by the generated code (OTP `:json`) | `{:ok, id}` (integer) or `{:error, reason}` |
| `BeamlDb.get(table, type, key)` | as before | `{:ok, %{"id" => id, "version" => v, "value" => json}}`, `{:ok, nil}` or `{:error, reason}` |
| `BeamlDb.list(table, type, query)` | as before | `{:ok, [%{"id" => id, "version" => v, "value" => json}]}` or `{:error, reason}` |

- `json` in a returned row is a binary (the host reads `value::text`). The generated code decodes it with `:json.decode/1`. A decode raise is `"decode"`. A non-binary `value` is `"decode"`.
- The core uses `:null` for every JSON null (`reason`, a failed `value`), never `nil`. **[Observed]** by the plan check: `:json.encode(nil)` writes `"nil"`. → By: Opus (PLAN repair P3/P4) · Undo
- The host stores the binary as `$3::jsonb`. The host never encodes a core.
- The fake `BeamlDb` stores the binary as given and returns it as given. It no longer round-trips a map. PDB-10 and PDB-11 change so.
- **N2 (changed).** The fake got one put with `is_binary(json)`. The test decodes it with `:json.decode` and asserts the PDB-14 key set and values on that map; `reason == :null`.
- 0005 gets the tie test **N2c**: after N2, `jsonb_typeof(value->'reason') = 'null'` for the one row (appended to the 0005 plan). → By: Fable · Repair

### O3: PDB-09 withdrawn; D6B-39 holds for ROW TYPES

→ By: Fable · Repair, because DL-144 says avoid a parked item (D036 M4), never decide it.

- PDB-09 is withdrawn. The db check branch applies D6B-39 as built: a constructor or enum field cannot stand in a ROW TYPE with a MIGRATE CHAIN or a VERSION MARK. Texts: the built D6B-39 texts (main.rs HEAD lines 1593 and 1605, `effect <op>: the constructor field <R>.<f> ...` and `the enum field ...`), with their help lines. → By: Opus (PLAN repair P3/P4) · Undo
- The Checks table row "MIGRATE CHANGE on a constructor or enum field" is replaced by these two texts. N12 asserts them with `slice6/db/order_v2/orders.beaml` (the 0005-style v2 `Order` with `amount: Amount`, `channel: Channel` and `add note`): exit non-zero, the constructor text for `Order.amount` (first field in source order). **[Unknown]** which of the two texts fires first; the RED worker records it.
- The versioned decode is not joined with the DL-101 tail. The Limit on that join is withdrawn.
- **N5 and N20 (changed).** They use a String-only ROW TYPE: `slice6/db/plain/orders.beaml` with `type Order { order_id: String label: String }`, and `plain_v2/orders.beaml` with `type Order v2 { order_id: String label: String note: String }` and `migrate Order v1 -> v2 { add note: String = "" }`. Same assertions as before. D6B-39 allows this chain (no constructor or enum field). → By: Opus (PLAN repair P3/P4) · Repair
- **N18 (changed).** The help line stays pinned to today's text, the built RESPONSE RECORD constructor help (main.rs HEAD line 4903): `  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of Order (DL-102)`. The new row help "these rows ... (DL-102, DL-137)" is withdrawn. No new help wording, so M4 is not decided. → By: Fable · Repair

**[Verified] Finding against the ruling premise (for the main agent).** The ruling says the 0005 v2 `Order` (N7, N7b) is an `add` of a String field "which D6B-39 allows". The built D6B-39 check (main.rs HEAD lines 1582 to 1605) bans any constructor or enum field in a TYPE with a MIGRATE CHAIN, not only a change that names one. The 0005 `Order` holds `amount: Amount` (constructor) and `channel: Channel` (enum). So the 0005 `order_v2` variant is a compile error under D6B-39, and P4 builds no exception (PDB-09 withdrawn). See the 0005 correction and QDB-8 in [decisions.md](decisions.md#plan-repair-after-plan-check-2026-11-07).

### Medium notes

- **M-a (list-item literal check).** **N25b (new, RED).** An `orders.list` record with item 0 `channel "app"` under `no_app/orders.beaml`: exit 1 with the DL-122 RESPONSE RECORD text for `orders.list`. Control: item 0 `channel "tv"` with `unknown_fields ["items.0.channel"]`: exit 0. Without it, a reader that skips list items for literals passes. → By: Opus (PLAN repair P3/P4) · Undo
- Limit: the list-item literal check rests on N25b only; a list of more than one item with a lost literal in item 1 is not tested. → By: Opus (PLAN repair P3/P4)
- **M-b (stale put/4).** The 0005 plan gets a dated correction line: `BeamlDb.put/3` (QDB-2, with the JSON binary of O2). Q5-8 reads as put/3. → By: Fable · Repair
- PDB-18 (`items.<i>.<field>`) and PDB-24 (`rows: N rows, K checked, M not decodable`) are big (record format) and are listed in the 0005 owner review. → By: Fable · Repair
