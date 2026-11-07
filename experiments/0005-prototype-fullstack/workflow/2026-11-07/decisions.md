# Decisions: EXPERIMENT 0005 (PROTOTYPE: Postgres, BEAML, LiveView)

**[Proposal]** PLAN phase, 2026-11-07. Decisions that DL-126 to DL-144 do not settle.
Classes follow Decision4. DL-144 (free run): every Migrate question below has a built default, pinned by a test in RED and GREEN, and stays open until the OWNER signs it off (DL-139 rule). "Big" marks a default that touches syntax, a record format or a host-called name; [owner-review.md](owner-review.md) lists them first.
Every entry carries a `By:` line (DL-107). Workers record each taken default again in their `notes.md`.
ID check: no `P5-` or `Q5-` ID exists in `experiments/` or `wiki/` at this plan (grep).

## OWNER questions (Migrate, default built)

### Q5-1 · Migrate · big · The `db.get` key

- **A.** The row `id` (bigint) that `db.put` returns. Input TYPE `type OrderKey { id: Int }`. No new syntax; a host column becomes a BEAML field.
- **B.** A field of the TYPE names the key, for example `db.get("records", order_id)`. The host function looks up `value->>'order_id'` with a unique index per TYPE. The domain owns its identity; new syntax in the transport call.
- **Default: B**, because the identity belongs to the domain TYPE (DL-126) and a host row id would leak into BEAML. **Not built in 0005**: no source line uses `db.get` (P5-05); the host function `BeamlDb.get/3` exists with the B signature.
- → By: Opus (PLAN exp0005, default, open)

### Q5-2 · Migrate · `db.list` order and limit

- **A.** Fixed in the host function: `ORDER BY inserted_at DESC, id DESC LIMIT 100`. `OrderQuery` stays empty.
- **B.** Fields in the query TYPE: `type OrderQuery { limit: Int order: ListOrder }` with an enum `ListOrder`. A new order is a field (DL-129).
- **Default: A**, because the slice needs one order, and B puts an `Int` into an entry input (the open String-to-Int question of slice 6d). B follows when a page needs a second order. Pinned by N5.
- → By: Opus (PLAN exp0005, default, open)

### Q5-3 · Migrate · big · The List TYPE

- **A.** A list field form inside a record: `type OrderList { items: [Order] }`. The `db.list` head returns a record.
- **B.** A list declaration: `list OrderList of Order` (new keyword); the head returns `OrderList`, generated as an Elixir list.
- **Default: A**, because it needs no new top-level keyword, every EFFECT head keeps a record output, and a later cursor or count is one more field. Built in P4; pinned by N5.
- → By: Opus (PLAN exp0005, default, open)

### Q5-4 · Migrate · big · How `--stored` reads the Postgres rows

- **A.** The compiler connects itself: `beaml-spike SOURCE --stored-db` runs `psql` with the connection from `DATABASE_URL` or the socket default and reads the rows as JSON lines. The compiler process holds the connection.
- **B.** A host Mix task `mix beaml.stored SOURCE` queries the rows through the Repo at build time, writes a row RECORD SNAPSHOT to a temp file and runs `beaml-spike SOURCE --stored <file>`. The compiler stays file-only.
- **Default: B**, because the compiler gets no database client and no connection value; the Repo config is the one connection place; the read is live at build time (DL-094, DL-127). Big: the row snapshot is a record format (keys `type`, `version`, `value`, `id`), and `mix beaml.stored` is a host-called name. Built in P4; pinned by N7 and N8.
- → By: Opus (PLAN exp0005, default, open)

### Q5-5 · Migrate · Where generated code lives in the Mix project

- **A.** `app/lib/generated/orders.ex`, checked in, written by `run.py gen`. A diff shows every generated change; the host builds without the compiler.
- **B.** A Mix compiler `:beaml` in `compilers:` that runs `beaml-spike` at `mix compile` and writes to `_build`; nothing generated in git.
- **Default: A**, because it needs no Mix compiler code, the change is reviewable, and N10 still holds (the regenerate step deletes `ui_place/1`). B follows when a second source or a watcher is needed.
- → By: Opus (PLAN exp0005, default, open)

### Q5-6 · Migrate · big · The generated module name

- **A.** From the source file stem: `orders.beaml` → `defmodule Orders`; nested `Orders.Rejected`, `Orders.Order`.
- **B.** A declaration line in the source: `module Orders`.
- **Default: A**, because it adds no syntax and matches the DL-131 call `Orders.ui_place(params)`; the span service name already comes from the stem. Today every build is `BeamlSpike` (main.rs line 2674). Built in P5; pinned by N1. **[Inference]** The 0004 byte pins move (four guard sites, see memory note); P5 moves them with a diff proof.
- → By: Opus (PLAN exp0005, default, open)

### Q5-7 · Migrate · big · Where the capture streams live (ENTRY RECORDS, db call records)

- **A.** JSONL files through `ProbeSupport.Capture` in a capture directory per run (`results/<UTC>/capture/entries.jsonl`, `effects.jsonl`). The `records` table holds domain rows only.
- **B.** Rows in the `records` table with `type` = the stream (`"entry"`, `"effect"`), so one store holds everything.
- **Default: A**, because the table then means one thing (STORED ROWS of domain TYPES), `--stored` reads rows and capture records from separate sources, and the 0004 capture path stays unchanged. Big: storage of record formats (DL-143). Pinned by N3.
- → By: Opus (PLAN exp0005, default, open)

### Q5-8 · Migrate · big · The host DB module name and functions

- **A.** `BeamlDb.put(table, type, version, value)`, `BeamlDb.list(table, type, query)`, `BeamlDb.get(table, type, key)`; each returns `{:ok, _}` or `{:error, reason}`.
- **B.** A configured module: `config :beaml, db: Proto.Store`, called through `Application.fetch_env!/2`, with a behaviour the host implements.
- **Default: A**, because DL-129 names `BeamlDb`, a fixed remote call fails the host build when the module is missing (same reason as DL-131), and there is one implementation (no behaviour for one product). Built in P4; pinned by N2 and N5.
- → By: Opus (PLAN exp0005, default, open)

### Q5-9 · Migrate · big · How the list page loads its data

- **A.** A second ENTRY LINE `effect ui.orders OrderQuery -> OrderList ! StoreError = ui.event("orders") |> list_orders`; `OrderListLive.mount/3` calls `Orders.ui_orders(%{})`. A page load is treated as a UI EVENT named `orders`.
- **B.** A new inbound transport for a page load, for example `ui.mount("orders")`, with its own generated name.
- **Default: A**, because it adds no syntax and gives the list flow its root span and ENTRY RECORD through the slice 6d path. Big: `ui_orders` is a host-called name and "mount is an event" is a semantic choice. Needs P3. Pinned by N5.
- → By: Opus (PLAN exp0005, default, open)

## Undo and Repair decisions

Format: **ID · class · decision.** Chose / Over / Because. Commits us to (Repair only).

**P5-01 · Undo · Local database through `pg_ctl`, not `docker compose`.**
Chose: Postgres.app 17.11 `initdb` and `pg_ctl` with a data directory in `app/.pgdata`. Over: a Postgres image in `docker compose`. Because: the tools exist on the machine; no image download; no compose file with a password variable.
→ By: Opus (PLAN exp0005)

**P5-02 · Repair · Unix socket only, trust auth, no password; the OWNER runs `db-up` and `db-down`.**
Chose: `listen_addresses=''`, socket in `app/.pgsock`, `--auth=trust`; `config/runtime.exs` reads `DATABASE_URL` only when set. Over: a TCP port with a password. Because: no secret exists, so no worker can read or print one; the task rule gives the database to the OWNER. Commits us to: a password-bearing `DATABASE_URL` makes every step an OWNER step.
→ By: Opus (PLAN exp0005)

**P5-03 · Undo · `mix phx.new --no-assets`; the page loads the prebuilt Phoenix and LiveView JS from the deps.**
Chose: no esbuild, no tailwind. Over: the default asset pipeline. Because: it downloads no binaries and the tests do not run JS.
→ By: Opus (PLAN exp0005)

**P5-04 · Repair · No `secret_key_base` or `signing_salt` value in git.**
Chose: the GREEN worker replaces the generated values with a runtime value (random per start for dev and test, `SECRET_KEY_BASE` for prod) by an edit that prints nothing; N13 checks key presence only. Over: keep the generated dev keys. Because: owner secret rules; a generated key is a secret value. Commits us to: sessions do not survive a dev server restart.
→ By: Opus (PLAN exp0005)

**P5-05 · Undo · No `db.get` line in the 0005 source.**
Chose: `put` and `list` only. Over: all three transports. Because: no page needs a single order; the host function exists for DL-129. Add when a detail page exists.
→ By: Opus (PLAN exp0005)

**P5-06 · Repair · `probe_support` as a path dep on the 0002 app.**
Chose: `{:probe_support, path: "../../0002-http-correlation/apps/probe_support"}`. Over: a copy in `app/`. Because: one source of `span/5`, `event/2`, `Capture`. Commits us to: `plug_cowboy` and OpenTelemetry in the host; fallback if the umbrella paths conflict (RED probe): a copy under `app/lib/probe_support/` with a recorded diff of zero.
→ By: Opus (PLAN exp0005)

**P5-07 · Undo · Table columns.**
Chose: `id` bigint identity, `type` text, `version` integer, `value` jsonb, `inserted_at` utc_datetime_usec default now, index `(type, inserted_at)`. Over: uuid id. Because: DL-127 names the columns; bigint is the Ecto default.
→ By: Opus (PLAN exp0005)

**P5-08 · Repair · End-to-end tests with `Phoenix.LiveViewTest` and the SQL sandbox, not a browser.**
Over: browser automation. Because: deterministic, no new dependency, submits through the rendered form. Commits us to: JS defects are not covered (limit).
→ By: Opus (PLAN exp0005)

**P5-09 · Undo · One `run.py` with a result directory per run.**
Chose: the 0003 and 0004 runner pattern. Because: repository rule for EXPERIMENTS.
→ By: Opus (PLAN exp0005)

**P5-10 · Undo · The stricter `Amount` rejects value `"0"`; the failure TYPE is `BadAmount`.**
Over: a currency list. Because: one clause, expressible with today's patterns; the stored value `"0"` is easy to seed by a submit.
→ By: Opus (PLAN exp0005)

**P5-11 · Undo · TYPE names `OrderList` and `StoreError`.**
Over: `Orders` and `PlaceError` (the DL-130 sketch). Because: `Orders.Orders` would be confusing under Q5-6 A; one failure TYPE serves both db EFFECTS and both flows.
→ By: Opus (PLAN exp0005)

**P5-12 · Undo · The host shows a reject or a store error as a flash.**
Over: per-field errors. Because: `Rejected` carries a reason, not a field (DL-133). Per-field errors need a field key in `Rejected`, a later question.
→ By: Opus (PLAN exp0005)

**P5-13 · Undo · Host action events to `.beaml/actions.jsonl`.**
Chose: one event per `handle_event` and `mount`, with result and key count, no values. Because: AGENTS rule and the owner action-tracking rule.
→ By: Opus (PLAN exp0005)

**P5-14 · Repair · N7 and N8 run outside the SQL sandbox.**
Chose: `run.py` seeds rows with committed writes (a submit in a non-sandbox test or SQL), builds with `--stored`, then truncates `records`. Over: sandbox-only tests. Because: `mix beaml.stored` reads committed rows from another connection. Commits us to: these steps run serial, never in parallel with `mix test`.
→ By: Opus (PLAN exp0005)

**P5-15 · Repair · N9 is blocked; its smallest form is `quarantine amount`.**
Over: a `retire` or `redact` free (M5, M3) or a hand-built interim fate. Because: D026 keeps M3, M4, M5 parked until before the fate slice, and DL-102 gives no built MIGRATE STEP that frees a stricter constructor. Commits us to: 0005 shows the block, not the free, until P6. The N8 control (old source passes) is the only release shown.
→ By: Opus (PLAN exp0005)

**P5-16 · Undo · Entry input fields are Strings, constructor TYPES or enums only.**
Over: an `Int` field. Because: the String-to-Int coercion question of slice 6d stays open and is not needed.
→ By: Opus (PLAN exp0005)

**P5-17 · Repair · 0005 RED starts after P1 to P5 are GREEN and TESTED; the host skeleton is setup.**
Chose: the first behaviour RED is N2 on the missing `/orders/new` route. Over: a RED on `unsupported effect kind db.put`. Because: a prerequisite failure is not 0005 behaviour. Commits us to: 0005 waits for five steps.
→ By: Opus (PLAN exp0005)

## Plan repair (after plan check), 2026-11-07

**[Proposal]** Decisions of the repair of [plan-review.md](plan-review.md). Rulings by the main agent under DL-144 carry `By: Fable`. Earlier entries above stay.

### Q5-10 · Migrate · big · STORED ROW value shape

- **A.** The bare DL-105 projection of the TYPE in `value`; `type` = bare TYPE name; no `value_sha256`, no record core in the row.
- **B.** The record format v3 core (DL-143) in the row: `value` holds the core with the projection under its `value` key, `value_sha256`, and the head keys. The columns `type` and `version` stay for the query.
- **Default: B**, because DL-127 says a row is a record as in the JSONL store, and DL-143 wants one format for every stream. Big: a record format. Built in P4; pinned by N2. Needs P2.
- → By: Fable (default, open)

### Repair and Undo

**P5-18 · Repair · P2 changes record keys only.**
Chose: P2 builds the DL-143 core and extras; no failure struct as an input value (M8), the DL-124 block text keeps its line shape (M9). Over: P2 waits for D026. Because: P2 then decides neither parked item. Commits us to: a P2 worker that must change M8 or M9 stops and reports a blocker.
→ By: Fable

**P5-19 · Repair · N8b and N8c; every snapshot writes `snapshot-meta.json`.**
Chose: a data-side control (delete `order-zero`, rebuild, exit 0) and a provenance check (snapshot ids and count equal a fresh `psql` query; query time and row count in the result directory). Over: the source-side control only. Because: a stale or wrong snapshot gave the same exit (O2). Commits us to: writes stay still between the snapshot and the `psql` read.
→ By: Fable

**P5-20 · Repair · N8c also covers N7 and N7b; N7 asserts its seeded row id is in the snapshot.**
Over: N8 only. Because: N7 exit 0 is also true on an empty snapshot (O2 evidence).
→ By: Opus (PLAN repair exp0005)

**P5-21 · Repair · N7b: a submit under v2 writes a version-2 row; the list renders v1 and v2.**
Chose: N7b and the `to_order` change in `order_v2.beaml` (`note: ""`). Over: lazy read only. Because: the `put` side of a version change was unproven (O3).
→ By: Fable

**P5-22 · Undo · A worker may run `db-up` and `db-down`.**
Chose: worker step for the local trust-auth socket cluster. Over: OWNER step. Because: no secret exists; the OWNER step stopped a free run. P5-02 changes: the OWNER step stays only with a set `DATABASE_URL`.
→ By: Fable

**P5-23 · Undo · `unix_socket_permissions=0700` in `db-up`.**
Over: the default mode 0777. Because: only the OWNER user reaches the trust socket.
→ By: Opus (PLAN repair exp0005)

**P5-24 · Undo · Host setup lines for `probe_support`.**
Chose: `Capture` child and `ProbeSupport.setup/0` in `Proto.Application`; `:output` and `:service` in `runtime.exs`; the 0002 OTel config copied; the `lazy_html` NIF download recorded (source URL and sha256 only); the dep pins checked against Phoenix 1.8.5. Because: a path dep brings no umbrella config.
→ By: Fable

**P5-25 · Undo · Env variable name `BEAML_CAPTURE_DIR`, service `"orders"`.**
Because: `run.py` passes the capture directory per run; the name holds no secret.
→ By: Opus (PLAN repair exp0005)
