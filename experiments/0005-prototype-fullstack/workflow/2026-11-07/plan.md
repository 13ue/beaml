# Plan: EXPERIMENT 0005, the first full-stack PROTOTYPE (Postgres, BEAML, LiveView)

**[Proposal]** PLAN phase, 2026-11-07. Task records only. No production file, no test, no commit, no run.
Decisions: DL-126, DL-127, DL-128, DL-129, DL-130 to DL-134, DL-137, DL-139, DL-141 to DL-143 and DL-144 (free run) in [the decision log](../../../../wiki/planning/decision-log.md). Also read: the slice 6d [plan](../../../0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/plan.md) and its fixture `experiments/0004-generated-replay/slice6/entry/orders.beaml`; D036 in [decisions to be made](../../../../wiki/planning/decisions-to-be-made.md); the [later candidate](../../../../wiki/planning/research-and-development.md#later-candidate--ecto-and-liveview) in the register; `experiments/0001-syntax-to-beam/src/main.rs` (CLI, `--stored`, generated module) at HEAD 5b7feb92; `experiments/0002-http-correlation/apps/probe_support`.
Design decisions and OWNER questions: [decisions.md](decisions.md) (P5-01 to P5-17, Q5-1 to Q5-9). Walk-through list: [owner-review.md](owner-review.md).
By: Opus (PLAN exp0005) for every proposal in this file. Every Migrate question has a built default under DL-144: `By: Opus (PLAN exp0005, default, open)`.

Proposed terms (glossary entry in the docs phase before GREEN prose uses them): PROTOTYPE (EXPERIMENT 0005: one Phoenix app, one BEAML source, one table), STORED ROW (one row of the `records` table, owned by BEAML, DL-127), DB TRANSPORT (`db.put`, `db.get`, `db.list`, DL-129).

## Facts the plan builds on (observed at HEAD 5b7feb92)

- **[Verified]** The compiler CLI is `beaml-spike SOURCE.beaml [--stored SNAPSHOT.jsonl ...]`; Elixir goes to stdout (main.rs line 5598). `--stored` reads a JSONL file only. A source with an EFFECT needs `--stored` (line 4841).
- **[Verified]** The generated module is always `defmodule BeamlSpike` (line 2674). DL-131 writes the host call as `Orders.ui_place(params)`. The two differ (Q5-6).
- **[Verified]** `validate` allows one EFFECT: `slice 1 supports one effect` (line 1610). The only transport is `http.post` (line 1446). D6B-147 named several ENTRY LINES and EFFECTS as the first 0005 precondition.
- **[Verified]** The compiler has no list TYPE. TYPES are records, enums and `String`, `Int`.
- **[Verified]** Generated code calls `ProbeSupport.span/5`, `ProbeSupport.event/2`, `ProbeSupport.Capture.write/2` and `OpenTelemetry`. `probe_support` lives in the 0002 umbrella (`apps/probe_support`, deps `plug_cowboy`, `opentelemetry_api`, `opentelemetry`).
- **[Verified]** Slice 6d is at RED re-check PASS (commit 8ab33d8d). GREEN has not started. Its fixture `orders.beaml` holds the 0004 Orders domain with `Amount` (constructor), `Channel` (enum with `Unknown(String)`) and the ENTRY LINE form of DL-130.
- **[Verified]** No FATE OPERATION is built. A MIGRATE STEP with `rename`, `add`, `drop` exists (slices 2 and 3). Under DL-102 a stored value that fails a new constructor clause blocks the build; no built MIGRATE STEP frees it.
- **[Verified]** Local tools: Elixir 1.18.1 / OTP 27, `phx_new` 1.8.5, Postgres.app 17.11 (`initdb`, `pg_ctl`, `psql`), Docker, cargo. **[Unknown]** hex.pm access for `mix deps.get`.

## Prerequisites (separate implement-step tasks, in this order)

| ID | Step | What 0005 needs from it | Ledger |
|---|---|---|---|
| P1 | Slice 6d GREEN, TEST, review | ENTRY LINE, `ui_<event>/1`, `Rejected`, ENTRY RECORD with `outcome`, `reason`, both unknown lists | 0004 `slice6d-inbound-effect` |
| P2 | Record format v3 (DL-143) | one record core; the db stream uses it from the start | new, 0004 |
| P3 | Several ENTRY LINES and EFFECTS per source (D6B-147) | two entries, two db EFFECTS in one source; `Replay` selects by operation | new, 0004 |
| P4 | DB TRANSPORT step (DL-129) | see below | new, 0005 `workflow/<date>/db-transport/` |
| P5 | Module name per source (Q5-6 default A) | `defmodule Orders`; `Orders.Rejected` | new, 0004 |
| P6 | Fate slice, `quarantine` only (DL-125) | N9 only | **blocked**: D036 trigger says M3, M4, M5 come before the fate slice |

**P4 content (planned in its own PLAN, listed here so nothing is lost).**
- `db.put("records")`, `db.list("records")` and `db.get("records")` parse as transport kinds on `effect` lines.
- The generated EFFECT calls the host module (Q5-8 default `BeamlDb`): `BeamlDb.put(table, type, version, value)`, `BeamlDb.list(table, type, query)`, `BeamlDb.get(table, type, key)`. The host returns `{:ok, rows}` or `{:error, reason}`; generated code maps an error to the failure TYPE with `reason: "transport"`.
- `put` writes the DL-105 projection of the TYPE under String keys, with `type` = TYPE name and `version` = current TYPE VERSION.
- `list` decodes every row `value` by its own row `version`, applies the MIGRATE CHAIN to the current version (DL-127, DL-054 rule), then the DL-101 decode with constructors.
- Every db call writes one record in the v3 format (DL-143) to the capture stream (Q5-7 default A).
- `--stored` over rows (Q5-4 default B), with the DL-136 rule: only rows that `db.list` would decode are checked; the DL-124 text rule (no stored value printed).
- The List TYPE (Q5-3 default A).

## The BEAML source `experiments/0005-prototype-fullstack/src/orders.beaml` (default forms)

```
// EXPERIMENT 0005: the PROTOTYPE domain. BEAML owns TYPES, entries, flow and rows.
type BadAmount {}
type Amount { value: String currency: String }
fn Amount value: String, currency: String -> Amount ! BadAmount
fn Amount _, "" -> Amount ! BadAmount = BadAmount {}
fn Amount value, currency -> Amount ! BadAmount = Amount { value: value, currency: currency }

enum Channel { Web = "web"  App = "app"  Unknown(String) }

type PlaceForm { order_id: String amount: Amount channel: Channel }
type Order { order_id: String amount: Amount channel: Channel }
type OrderQuery {}
type OrderList { items: [Order] }
type StoreError { reason: String }

effect orders.save Order -> Order ! StoreError = db.put("records")
effect orders.list OrderQuery -> OrderList ! StoreError = db.list("records")

effect ui.place PlaceForm -> Order ! StoreError = ui.event("place") |> place
effect ui.orders OrderQuery -> OrderList ! StoreError = ui.event("orders") |> list_orders

fn to_order PlaceForm { order_id, amount, channel } -> Order =
  Order { order_id: order_id, amount: amount, channel: channel }

fn place f: PlaceForm -> Order ! StoreError = f |> to_order |> orders.save
fn list_orders q: OrderQuery -> OrderList ! StoreError = q |> orders.list
```

- **[Proposal]** `[Order]` is the Q5-3 default (big, syntax). `OrderList` avoids a struct `Orders.Orders` (P5-11).
- **[Proposal]** Variants used by tests: `src/variants/stricter.beaml` (N8: adds `fn Amount "0", _ -> Amount ! BadAmount = BadAmount {}` before the general clause), `src/variants/order_v2.beaml` (N7: `type Order v2 { ... note: String }` and `migrate Order v1 -> v2 { add note: String = "" }`), `src/variants/no_place.beaml` (N10: the `ui.place` line removed). Each is a full source, compared to `orders.beaml` by a diff in the ledger.

## Host project `experiments/0005-prototype-fullstack/app/` (host-owned)

- Generate once with `mix phx.new app --app proto --module Proto --no-mailer --no-dashboard --no-gettext --no-assets` (P5-03). **[Unknown]** the exact 1.8.5 flag set; the GREEN worker checks `mix help phx.new` first and records it.
- **Secrets (P5-04).** The generator writes `secret_key_base` and `signing_salt` values into config files. The GREEN worker replaces them without printing them (an in-place edit with no output) by a runtime value: `config/runtime.exs` sets a random `secret_key_base` per start for `:dev` and `:test`, and reads `SECRET_KEY_BASE` for `:prod`. No secret value goes into git. The worker never prints a config file before this edit.
- **Database (P5-01, P5-02).** `config/runtime.exs` reads the env variable `DATABASE_URL` when it is set (this plan defines the name; the code is the source of the name). When it is not set, the Repo uses `socket_dir: <app>/.pgsock`, user `proto`, database `proto_dev` or `proto_test`, no password. `.pgdata/` and `.pgsock/` are in `app/.gitignore`.
- **Deps.** Phoenix 1.8.5 defaults plus `{:probe_support, path: "../../0002-http-correlation/apps/probe_support"}` (P5-06). **[Unknown]** whether the umbrella `build_path`/`deps_path` of `probe_support` conflict as a path dep; the RED worker probes once; fallback in P5-06.
- **`priv/repo/migrations/<ts>_create_records.exs`**: one table `records`: `id` bigint identity primary key, `type` text not null, `version` integer not null, `value` jsonb not null, `inserted_at` utc_datetime_usec not null default now (P5-07). Index `(type, inserted_at)`.
- **`lib/proto/beaml_db.ex`**: `BeamlDb.put/4`, `list/3`, `get/3` over `records` with `Ecto.Adapters.SQL.query/3` (no Ecto schema, DL-127). `list` order and limit are the Q5-2 default.
- **`lib/generated/orders.ex`**: the compiler output, written by `run.py gen`, checked in (Q5-5 default A).
- **Router**: `live "/orders/new", OrderFormLive`, `live "/orders", OrderListLive`.
- **`OrderFormLive`**: a form with `order_id`, `amount[value]`, `amount[currency]`, `channel`. `handle_event("place", params, socket)` calls `Orders.ui_place(params["order"])`:
  - `{:ok, %Orders.Order{}}` → `push_navigate` to `/orders`;
  - `{:error, %Orders.Rejected{reason: r}}` → flash `"form rejected: " <> r`, form kept;
  - `{:error, %Orders.StoreError{reason: r}}` → flash `"store failed: " <> r`.
  The host never builds a domain struct and never passes a failure struct back (M8 untouched).
- **`OrderListLive`**: `mount` calls `Orders.ui_orders(%{})` (Q5-9 default A) and renders `items` (order_id, amount, channel literal). Errors render a flash (P5-12).
- **Action log (P5-13).** Every `handle_event` and every `mount` of the two pages appends one JSONL event to `<repo>/.beaml/actions.jsonl` (AGENTS rule): `ts`, `source: "ui"` (the server cannot tell mouse from key), `action` (`place` or `orders`), `target` (page), `result` (`ok`, `rejected:<reason>`, `store_error`), the key count of params. Never a form value, a path or source text. Logging never raises.

## Local database (OWNER step, P5-01)

**[Proposal]** `pg_ctl` with Postgres.app 17.11, not `docker compose`. `run.py db-up`:

```
initdb -D app/.pgdata -U proto --auth=trust          # first time only
pg_ctl -D app/.pgdata -o "-k <abs>/app/.pgsock -c listen_addresses=''" -l app/.pgdata/log start
createdb -h <abs>/app/.pgsock -U proto proto_dev; createdb ... proto_test
```

- Unix socket only, no TCP port, trust auth: no password exists, so nothing secret is created or read. `run.py db-down` stops it.
- **The OWNER runs `db-up` and `db-down`** (task rule: the OWNER provides the database). Workers run `run.py` (tests) only against a database that is up; when it is down, `run.py` fails with `ERROR DATABASE: not reachable at app/.pgsock. Run run.py db-up.` and records `fail`, not `skip`.
- If the OWNER sets `DATABASE_URL` (for example a password-bearing database), **the OWNER runs every step**; workers never read, print or pass the value.

## N-tests

Host tests in `app/test/prototype_test.exs` (`Phoenix.LiveViewTest`, `Ecto.Adapters.SQL.Sandbox`), compiler-level cases in `experiments/0005-prototype-fullstack/tests/prototype_test.py`, both driven by `run.py`. Expected values come from this plan and the DL entries, never from the new compiler output.
`good = %{"order_id" => "order-1", "amount" => %{"value" => "12.50", "currency" => "EUR"}, "channel" => "web"}`.

- **N1 (generate and host build).** `beaml-spike src/orders.beaml --stored <rows>` exits 0 on an empty table; `app/lib/generated/orders.ex` holds `defmodule Orders`, `def ui_place(`, `def ui_orders(`; `mix compile --warnings-as-errors` exits 0.
- **N2 (first RED: form submit → row).** `live(conn, "/orders/new")`, `form("#place", order: good) |> render_submit()` navigates to `/orders`. Exactly one row in `records` (read with a separate SQL query): `type = "Order"`, `version = 1`, `value = {"order_id":"order-1","amount":{"value":"12.50","currency":"EUR"},"channel":"web"}`. Today: no route `/orders/new` (genuine RED: the page is the behaviour; a missing dep or a compile error is not RED).
- **N3 (records of the submit).** After N2 the capture stream holds one ENTRY RECORD (`operation: "ui.place"`, `outcome: "accepted"`, `reason: null`, `unknown_keys: []`) and one db record (`operation: "orders.save"`) in the v3 format; both share `trace_id`. No form value outside `value`.
- **N4 (reject: zero writes).** Currency `""`: the page shows `form rejected: constructor`; zero rows; one ENTRY RECORD with `outcome: "rejected"`, `reason: "constructor"`; no `orders.save` record. Channel `"tv"` is accepted as `Unknown("tv")` and stored as `"tv"`.
- **N5 (list page over `db.list`).** After submits `order-1` then `order-2`, `/orders` shows both, in the Q5-2 default order (`order-2` first). The test reads the page only, never the table.
- **N6 (`Unknown` round trip).** The row with channel `"tv"` lists as `tv`.
- **N7 (MIGRATE CHAIN on read).** Seed one v1 row by SQL. Generate from `variants/order_v2.beaml`. `--stored` exits 0 (the `add` maps v1). `/orders` lists the row with `note` `""`. The row in the table still has `version = 1` (lazy, on read).
- **N8 (stricter `Amount` blocks against live rows).** Submit `order-zero` with value `"0"` under `orders.beaml`. Build `variants/stricter.beaml` with `--stored` over the live table: exit non-zero; stderr names `Order`, the field `amount` and the constructor; stderr contains neither `order-zero` nor the stored value (DL-124). The Ecto migration directory is unchanged (hash). No assertion on the help line (M4) or on the number of record lines (M9).
  - **Control.** The same build with `orders.beaml` exits 0 (the block comes from the TYPE change, not from the data).
- **N9 (a MIGRATE STEP frees N8). BLOCKED.** Smallest form: `migrate Order v1 -> v2 { quarantine amount }` (DL-125 form 1), then `--stored` exits 0 and `/orders` omits `order-zero`. Needs P6, and P6 waits for M3, M4, M5 (D036). `run.py` reports `blocked: fate slice (D036)`, never `pass`. `quarantine` itself touches no parked question; `retire` (M5) and `redact` (M3) are not offered.
- **N10 (removed entry stops the host build).** Generate from `variants/no_place.beaml`; `mix compile --warnings-as-errors` exits non-zero and names `Orders.ui_place/1` (DL-131). **[Unknown]** until the slice 6d RED probe result for Elixir 1.18.1; if the compiler only warns, `--warnings-as-errors` still fails, which is the assertion.
- **N11 (no DDL from a TYPE change).** Across N7 and N8, `priv/repo/migrations/` and the `records` columns (`information_schema.columns`) stay equal to the N1 state.
- **N12 (action events).** After N2 and N4, `.beaml/actions.jsonl` has one event per action with `result` `ok` and `rejected:constructor`; no line contains `order-1`, `12.50`, `EUR`, a path or source text. Compiler events follow the existing harness check.
- **N13 (no secret in git).** `git ls-files app` holds no `.pgdata`, `.pgsock` or env file; `app/config/*.exs` hold no `secret_key_base:` or `password:` literal (a key-presence check that prints only file and line number, never a value).

## Existing assertions that change

- None in 0004 or 0001 from 0005 itself. P1 to P5 carry their own change tables.

## Checks

- 0005: `python3 -B experiments/0005-prototype-fullstack/run.py` (N1 to N13), `mix format --check-formatted` in `app/` excluding `lib/generated/`.
- 0001 and 0004: unchanged by 0005; the prerequisite steps run their own suites.

## Order

1. P1 → P2 → P3 → P5 → P4 (each its own ledger, one code-writing worker at a time).
2. 0005 Solve/RED: host skeleton (generator, secret edit, deps, migration) is setup, not behaviour; then RED N2 on the missing route.
3. 0005 GREEN, TEST, review, docs. N9 stays blocked until P6.

## Where 0005 touches the parked D036 items

| Item | Touch | Plan |
|---|---|---|
| M3 (DL-116, `redact` scope) | none | no `redact`, no redacted field |
| M4 (DL-102 help text) | N8 prints a block | assert exit, names and absence of values only, not the help line |
| M5 (`retire` semantics, binds DL-127 rows) | N9 could use `retire` | not offered; `quarantine` only, and N9 blocked |
| M8 (failure struct as a value at the host) | the host receives `StoreError`, `Rejected` | the host only matches; never passes one into generated code |
| M9 (record lines in the DL-124 text) | N8 with one stored row | no line-count assertion |

## Register row draft (do not edit the register in PLAN)

```
| [0005: PROTOTYPE full stack](../../experiments/0005-prototype-fullstack/README.md) | Can one BEAML source own the TYPES, the UI EVENT entry, the flow and the rows of a LiveView page in one JSONB table, so that a TYPE change blocks the build against the live rows with no second migration system? | LANGUAGE/COMPILATION, EXECUTION (host: Phoenix, Repo, LiveView) | **[Proposal]** PLAN 2026-11-07, free run (DL-144); prerequisites P1 to P5 open, N9 blocked by D036. [Plan](../../experiments/0005-prototype-fullstack/workflow/2026-11-07/plan.md). |
```

## Exclusions

As in the [README](../../README.md#exclusions). Also: no Docker image, no TCP database, no browser automation, no deploy.

## Limits

- **[Inference]** `Phoenix.LiveViewTest` runs the server side of the page, not the JavaScript. A form name mismatch in HEEx is caught (the test submits through the rendered form), a JS defect is not.
- **[Inference]** The SQL sandbox runs each test in a transaction. N8 builds against rows a test committed; the `--stored` read needs those rows outside the sandbox. `run.py` runs N8 and N7 as a non-sandbox step: it submits through a running test, commits, then builds (detail for the RED worker, P5-14).
- **[Unknown]** Whether `probe_support` works as a path dep outside its umbrella (P5-06).
- **[Unknown]** The cost of `--stored` over the live table (one full scan of `records` per build). Fine for a PROTOTYPE; a measure decides later.
- **[Inference]** P4 is the largest prerequisite. Its plan may split it (put and list first, `--stored` over rows second).

## Plan repair (after plan check), 2026-11-07

**[Proposal]** Repair of the BLOCK in [plan-review.md](plan-review.md) (O1 high, O2 high, O3 medium). Earlier text above stays; this section replaces it where the two differ. Rulings by the main agent under DL-144: `By: Fable`. Other lines: `By: Opus (PLAN repair exp0005)`. Decisions: [decisions.md](decisions.md#plan-repair-after-plan-check-2026-11-07).

### O1 · P2 changes record keys only (M8, M9 avoided)

- **P2 (record format v3) scope.** P2 changes the keys of the records only: the common core of DL-143 (head keys, `value` + `value_sha256`, `outcome` + `reason`, `unknown_keys` + `unknown_fields`, `redacted`, span id) and the transport extras.
- **P2 does not touch M8.** Generated code accepts no failure struct as an input value. The host value rule stays as built.
- **P2 does not touch M9.** The DL-124 block text keeps its current line shape. P2 adds no per-record line and no new line count.
- P2 meets the D036 trigger "before the record format v3 step (M8, M9)". Because P2 avoids both, P2 does not wait. M8 and M9 stay open and parked. A P2 worker that finds it must change either one stops and reports a blocker.
- → By: Fable · class Repair

Replacement row for the D036 table:

| Item | Touch | Plan |
|---|---|---|
| M8 (failure struct as a value at the host) | the host receives `StoreError`, `Rejected`; P2 changes record keys | the host only matches; P2 adds no input path for a failure struct |
| M9 (record lines in the DL-124 text) | N8 with one stored row; P2 record keys | no line-count assertion; P2 keeps the block text line shape |

### O2 · N8 and N7 prove a live read

Every `--stored` build over Postgres (`mix beaml.stored`, Q5-4 default B) writes its snapshot to a new file in the result directory. It also writes `snapshot-meta.json` beside it: the query time (UTC, from `SELECT now()` in the same transaction), the database name, the row count and the sorted row ids. No row value goes into the meta file.

- **N8b (data-side control).** After N8, delete the `order-zero` row by SQL. Run the same stricter build through `mix beaml.stored` again: exit 0. The block came from the data, not from a stale file.
- **N8c (snapshot provenance).** For every snapshot in N7, N7b, N8 and N8b: the file did not exist before the step; its row ids and count equal a fresh `psql` query of `records` ids at the same instant (the test holds writes still between the two reads). Compare ids and count only; print no values. N7 also asserts that the seeded v1 row id is in its snapshot before the exit-0 check.
- → By: Fable · class Repair (N8b, N8c, the meta file)
- → N8c applied to N7 and N7b as well · By: Opus (PLAN repair exp0005) · class Repair

### O3 · N7b, a write under v2

- **N7b (v2 write, mixed read).** Under `variants/order_v2.beaml`, submit `order-3` through the page. One new row has `version = 2` and `value.note = ""`. `/orders` lists the v1 row (from N7) and the v2 row together. N11 columns are still unchanged.
- **Variant change.** `order_v2.beaml` also changes `to_order`: it builds `Order { order_id: order_id, amount: amount, channel: channel, note: "" }`. The variant diff in the ledger shows this line.
- → By: Fable · class Repair

### Q5-10 · STORED ROW value shape

New big OWNER question, see [decisions.md](decisions.md#q5-10--migrate--big--stored-row-value-shape). Default B: the record format v3 core goes into the row `value`. P4 builds it; N2 then asserts the projection inside the core (`value.value` equals the old N2 object) and `value_sha256`, not a bare projection. The N2 expectation above changes accordingly in RED.
- → By: Fable (default, open) · class Migrate

### Local database: a worker may run `db-up` and `db-down`

- The local `pg_ctl` cluster has trust auth on a Unix socket only and holds no secret. A worker may run `run.py db-up` and `run.py db-down`. → By: Fable · class Undo
- `db-up` adds `-c unix_socket_permissions=0700` to the `pg_ctl -o` options. → By: Opus (PLAN repair exp0005) · class Undo
- The OWNER-step rule stays only when `DATABASE_URL` is set (P5-02 commitment).
- The test run (`run.py` without a subcommand) never starts or stops the database. When it is down, it fails as written above.

### Host setup lines (setup, not behaviour)

A path dep brings no umbrella config. The 0005 host sets these itself:

- `Proto.Application` starts `ProbeSupport.Capture` as a child and calls `ProbeSupport.setup/0` at start.
- `config/runtime.exs` sets `:probe_support, :output` to the capture directory of the run (`results/<UTC>/capture/`, passed by `run.py` in a non-secret env variable that this plan names `BEAML_CAPTURE_DIR`) and `:probe_support, :service` to `"orders"`.
- `config/config.exs` copies the OTel config of the 0002 umbrella: `resource_detectors`, `sampler: :always_on`, `processors: [{:otel_simple_processor, %{exporter: {ProbeSupport.Exporter, %{}}}}]`, `text_map_propagators: [:trace_context]`.
- `probe_support` pins `plug_cowboy == 2.8.1`, `opentelemetry_api == 1.5.0`, `opentelemetry == 1.7.0`. The setup worker checks that `mix deps.get` resolves them with the Phoenix 1.8.5 deps and records the lock diff.
- `lazy_html` (needed by `Phoenix.LiveViewTest` in 1.8) downloads a precompiled NIF at build. The setup worker records the download in the result directory: source URL and sha256 only.
- → By: Fable · class Undo (setup lines); `BEAML_CAPTURE_DIR` and `:service` value · By: Opus (PLAN repair exp0005) · class Undo

### Acceptance (replaces the README line)

One `run.py` run passes N1 to N7, N7b, N8, N8b, N8c and N10 to N13 with exit 0 and retains its result directory. N9 is `blocked`, never `pass`.
