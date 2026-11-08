---
id: experiment-0005-prototype-fullstack
kind: experiment
status: verified
updated: 2026-11-08
revision: 3 (docs after TEST PASS)
---

# EXPERIMENT 0005 — PROTOTYPE: Postgres, BEAML, LiveView

**[Verified]** TEST PASS on 2026-11-08: GREEN `d4e11f78`, TEST `0315cf2f`. Run [20261108T003740313204Z](results/20261108T003740313204Z/result.json): status `pass`, 16 of 16 steps exit 0, 19 use cases pass, N9 `blocked: fate slice (D036)`. A second run [20261108T003757953791Z](results/20261108T003757953791Z/result.json) gives the same ([TEST review](workflow/2026-11-08/review.md)). A PROTOTYPE pass does not establish production readiness.
By: Opus (docs exp0005) for the result sections. The plan sections below keep their PLAN authors.

## Result (2026-11-08)

### Who owns which step

**[Verified]** As built and observed by N3, N5, N7, N7b ([GREEN output](workflow/2026-11-08/green-output.md#what-exists)).

| Step | Owner | Where |
|---|---|---|
| Form page `/orders/new`, list page `/orders`, notes page `/notes` (HEEx, router) | host | `app/lib/proto_web/live/` |
| Decode of the params, root span, ENTRY RECORD, `Rejected` struct | BEAML (generated) | `Orders.ui_place/1`, `ui_orders/1`, `ui_note/1`, `ui_notes/1` |
| Flow, constructors (`Amount`), enum literals (`Channel`) | BEAML (generated) | `app/beaml/orders.beaml` → `app/lib/generated/orders.ex` |
| ROW CORE encode, row decode, MIGRATE CHAIN on read, db call record | BEAML (generated) | `db.put`, `db.list` EFFECT lines |
| SQL over the one table `records` | host | `BeamlDb.put/3`, `list/3`, `get/3` in `app/lib/proto/beaml_db.ex` |
| One Ecto migration, Repo, local Postgres cluster | host | `app/priv/repo/migrations/`, `run.py db-up` |
| ROW SNAPSHOT of the live rows | host | `mix beaml.stored DIR` |
| `--stored` check of the snapshot (constructors, literals, chain) | BEAML (compiler) | `beaml-spike ... --stored` |
| Action log, one event per page action, no value | host | `app/lib/proto_web/action_log.ex` → `.beaml/actions.jsonl` |

### Tested flow

**[Verified]** Three paths, all through the generated functions:

```
form submit  → Orders.ui_place/1 (decode, ENTRY RECORD) → flow → db.put → BeamlDb (SQL) → row
list mount   → Orders.ui_orders/1 → db.list → BeamlDb (SQL) → row decode → page renders the BEAML value
v1 rows     → order_v2 source (Order v2 `add note`, Note v2 `add tag`) builds against them → list reads them through migrate (note "", tag "") → v2 submits write version 2
live rows    → mix beaml.stored (ROW SNAPSHOT) → compiler --stored → stricter Amount blocks, delete frees
```

### Actual results

**[Verified]** Run [20261108T003740313204Z](results/20261108T003740313204Z/result.json), [use cases](results/20261108T003740313204Z/use-cases.jsonl):

| Use case | What it proves | Result |
|---|---|---|
| N1, N10 | `orders.beaml` gives the module `Orders`; a removed `ui.place` stops the host build at `Orders.ui_place/1` | pass |
| N2, N2c, N3 | one submit writes one `Order` row through `db.put`, one ENTRY RECORD and one db record in one trace; `reason` is JSON null | pass |
| N4 (2) | a constructor reject writes no row; an unknown channel is stored as its text | pass |
| N5, N6 | the list reads through `db.list`, newest first; an Unknown channel lists as its text | pass |
| N7 (3), N7b (2) | `order_v2` builds against live v1 `Order` and `Note` rows; the v1 `Order` row (enum and constructor fields) lists as v2 with `note: ""` and stays version 1; the `Note` control lists with `tag: ""`; a v2 submit writes version 2 for both | pass (M4 step 1 run [20261108T081341856399Z](results/20261108T081341856399Z/result.json); this run had the String-only `note_v2` form, 2 + 1 cases) |
| N8 (2), N8b, N8c | a stricter `Amount` blocks the build against the live row and prints no stored value; control builds; delete by SQL frees; snapshot ids equal the live ids | pass |
| N11 | the TYPE change reached the table, the DDL did not move | pass |
| N12, N13 | one action event per action, no value; no secret literal in `lib/` or `config/` | pass |
| N9 | `quarantine amount` frees the stricter build | blocked: fate slice (D036) |
| N14 | variant [`rename_channel`](app/beaml/variants/rename_channel/orders.beaml) (`rename channel -> source` onto the ENUM field, DL-166) builds against the live v1 rows; stderr exactly `rows: 2 rows, 2 checked, 0 not decodable` | pass (fates a1b run [20261108T123541367741Z](results/20261108T123541367741Z/result.json), [0004 section](../0004-generated-replay/README.md#fates-step-a1b-rename-onto-enum-and-constructor-fields-quarantine-per-field-dl-166-dl-172)) |
| N15 | a `jsonb_set` changes one live row value without a new digest; `live_build` exits 1, no stdout, first line the digest error (DL-164); no stored value, order id, trace id or span id in stderr; no DDL; control: the row deleted, the build passes | pass (P2b run [20261108T134104848998Z](results/20261108T134104848998Z/result.json), [0004 section](../0004-generated-replay/README.md#step-p2b-a-wrong-digest-stops-the-build-dl-164)) |

**[Verified]** Output hashes of this run: `orders.ex` `f32433c8…51c7`, `note_v2` `b0990620…30c1c4`. M4 step 1 (DL-153) replaced the `note_v2` variant by [`order_v2`](app/beaml/variants/order_v2/orders.beaml); `gen-order_v2` output `3302ade3…fa04` (GREEN and TEST equal), `gen-order_v2.stderr`: `rows: 2 rows, 2 checked, 0 not decodable`.

**[Verified]** M4 step 1 run [20261108T081341856399Z](results/20261108T081341856399Z/result.json) (TEST m4-lift, compiler `6118f4c4…0d71`): 17 steps pass, 21 use cases pass, N9 blocked; `mix test` 29 tests, 0 failures. A v1 `Order` row inserted by hand into `proto_dev` lists on the running dev server with the `order_v2` module; the `orders.list` RESPONSE RECORD holds `note: ""`, the row stays version 1 ([TEST review (e)](../0004-generated-replay/workflow/2026-11-08/m4-lift-d6b39/review.md)). The `/orders` page has no note column (review O1).

### Screens

**[Verified]** Local server, demo rows written through `Orders.ui_*`, headless Chrome, dark mode ([TEST review §4](workflow/2026-11-08/review.md#4--screens-owner-visual-check)). Visual check only, not evidence for the thesis.

→ [Form `/orders/new`](workflow/2026-11-08/screens/orders-new.png)
→ [List `/orders`](workflow/2026-11-08/screens/orders.png)
→ [Notes `/notes`](workflow/2026-11-08/screens/notes.png)

### Limits

→ **[Verified]** N9 blocked until the fate slice: `quarantine amount` needs a fate form (M3, D036). M4 no longer blocks it (DL-153).
→ **[Verified]** The chained read runs on the real `Order` since M4 step 1 (DL-152, DL-153); `Note` stays the String-only control. A MIGRATE STEP that names `amount` or `channel` waits on M3.
→ **[Verified]** O1: `run.py run` truncates `proto_dev` and `proto_test`; rows made by hand are lost, and the shipped `orders.ex` is checked against 0 rows. N8 proves the gate in `proto_test` only.
→ **[Verified]** O2: `BeamlDb.get/3` matches the raw stored JSON, not the migrated value; an empty key returns any row. No source line uses `db.get`.
→ **[Verified]** O3: the list page calls the internal name `Orders.__beaml_encode_order/1`; a compiler rename breaks the host build.
→ **[Verified]** The form inputs are invisible in dark mode (no border, no background).
→ **[Inference]** The R1 guard is a text scan of `lib/proto_web`; it does not catch `BeamlDb.` or `Ecto` there.
→ **[Requirement]** Demo only: local cluster, no deploy, no real data, no browser test (DL-144).

### Smallest next test

**[Proposal]** O3 first: the compiler emits `Orders.project_order/1` for an ENTRY LINE output TYPE; the R1 guard adds "no `__beaml_` in `lib/proto_web`"; one test asserts the DL-105 projection. The OWNER chooses A or C first (D037, item 2). By: Opus (docs exp0005).

### Open decisions

**[Proposal]** Every built default is open for the OWNER walk-through: [owner-review.md](workflow/2026-11-07/owner-review.md), register D037 in [Decisions to be made](../../wiki/planning/decisions-to-be-made.md#d037--experiment-0005-built-defaults-dl-144-walk-through).

## Plan (2026-11-07)

**[Proposal]** PLAN phase, 2026-11-07, repaired after the plan check ([plan-review.md](workflow/2026-11-07/plan-review.md), [repair](workflow/2026-11-07/plan.md#plan-repair-after-plan-check-2026-11-07)). Plan: [workflow/2026-11-07/plan.md](workflow/2026-11-07/plan.md). Decisions: [decisions.md](workflow/2026-11-07/decisions.md). OWNER walk-through: [owner-review.md](workflow/2026-11-07/owner-review.md).
Binding OWNER decisions: DL-126 to DL-134, DL-137, DL-139, DL-141 to DL-144 in [the decision log](../../wiki/planning/decision-log.md). DL-144 makes this a free run: every open Migrate question has a built default, marked `By: Opus (PLAN exp0005, default, open)`.
By: Opus (PLAN exp0005) for every proposal in the plan sections.

## Question

**[Requirement]** (DL-127, DL-128, DL-129) Can one BEAML source own the TYPES, the UI EVENT entry, the flow and the database rows of a Phoenix LiveView page, so that a TYPE change travels from the source to the stored rows and the build stops where it must, with no second migration system?

## Hypothesis

**[Proposal]**

1. A form submit on a LiveView page reaches BEAML only through a generated entry function (`ui_place/1`, DL-131). BEAML decodes the params, writes the ENTRY RECORD, calls `db.put` and returns a typed result or a `Rejected` struct (DL-133).
2. The list page reads the rows only through `db.list`. A row of an older TYPE VERSION is read through the MIGRATE CHAIN (DL-127).
3. A stricter `Amount` constructor makes `beaml build --stored` fail against the live rows (DL-102, DL-121, DL-137). The host Ecto migration does not change.
4. A removed ENTRY LINE fails the host build, not the running page (DL-131).

## Context ownership

| Step | Owner | What |
|---|---|---|
| TYPES, VERSIONS, constructors, enum literals, `migrate` | BEAML (LANGUAGE/COMPILATION) | `src/orders.beaml` |
| ENTRY LINES `ui.place`, `ui.orders` | BEAML | decode, root span, ENTRY RECORD, `Rejected` (generated) |
| EFFECTS `orders.save = db.put`, `orders.list = db.list` | BEAML | head TYPES, decode of rows, MIGRATE CHAIN on read, records of the db stream (generated) |
| `--stored` check over rows | BEAML | constructors and literals over the live rows (DL-137) |
| Mix project, Repo, config, deps | host | `app/` |
| One Ecto migration: table `records(id, type, version, value jsonb, inserted_at)` | host | never changed by a TYPE change (DL-127) |
| `BeamlDb` with `put/…`, `list/…` (and `get/…`, unused) | host | SQL over the one table (DL-129) |
| Router, LiveView `OrderFormLive`, `OrderListLive`, HEEx | host | `handle_event("place", …)` calls `Orders.ui_place/1` |
| Local Postgres | host (worker or OWNER, P5-22) | `pg_ctl` cluster, see prerequisites |

## Supported subset

- One BEAML source `src/orders.beaml`: `PlaceForm`, `Order`, `Amount`, `Channel`, `PlaceError`, `BadAmount`, `OrderQuery`, `Orders`.
- Two ENTRY LINES, two `db.*` EFFECTS, no HTTP EFFECT.
- Entry input fields are `String`, constructor TYPES or enums only. No `Int` field (the String-to-Int question of slice 6d stays open).
- `db.put` and `db.list` only. `db.get` has a host function and an open key question (Q5-1); no BEAML line uses it.
- One table, one Ecto migration, one Repo.
- End-to-end tests run in `mix test` with `Phoenix.LiveViewTest` and the Ecto SQL sandbox. No browser test.

## Exclusions

- `db.get`, filters in `OrderQuery`, pagination (Q5-1, Q5-2 defaults only).
- FATE OPERATIONS. N9 is BLOCKED until the fate slice (DL-125); D036 keeps M3 and M5 parked before that slice (M4 answered, DL-152).
- `redact`, `retire` and `redacted` fields (M3, M5 untouched).
- The host passes no failure struct back into generated code (M8 untouched).
- No assertion on the number of record lines in a block text (M9 untouched). No assertion on the DL-102 help wording (M4 answered by DL-152; its wording is QM4-3, open).
- HTTP route entries, deploy, releases, auth, real data, any network service. Answer-class: none (DL-144: local only).
- Ecto schemas per TYPE (DL-127 option E).
- JavaScript behaviour in a real browser. The OWNER may open the page by hand; that is not evidence.

## Acceptance criteria

**[Proposal]** One `run.py` run passes N1 to N7, N7b, N8, N8b, N8c and N10 to N13 with exit 0 and retains its result directory. N9 is reported as `blocked` with the reason, never as `pass`. Details: [plan.md](workflow/2026-11-07/plan.md#n-tests).

2026-11-07 (plan repair 2, QDB-8 B): N7 and N7b stay in this line. They run on the String-only ROW TYPE `Note` (v1 → v2 `add tag`), not on `Order`, which has no chain under the built D6B-39. Details: [plan repair 2](workflow/2026-11-07/plan.md#plan-repair-2-after-re-check-2026-11-07). → By: Fable · Repair

2026-11-08 (M4 step 1, DL-153): N7 and N7b run on `Order v2` (`add note: String = ""`) beside enum and constructor fields; `Note` stays as the small control. → By: Opus (m4-lift, docs) · Undo

## Repeatable command

```
python3 -B experiments/0005-prototype-fullstack/run.py db-up     # a worker or the OWNER, once per machine start
python3 -B experiments/0005-prototype-fullstack/run.py           # every run (= run); truncates proto_dev and proto_test (O1)
python3 -B experiments/0005-prototype-fullstack/run.py db-reset  # optional: empty both databases
python3 -B experiments/0005-prototype-fullstack/run.py db-down   # stop the cluster
```

`run.py` builds the 0001 compiler, generates `app/lib/generated/orders.ex`, runs `mix compile --warnings-as-errors`, `mix ecto.migrate`, `mix test`, the `--stored` cases and writes `results/<UTC>/` with commands, toolchain versions, input and output hashes and the actual results. The test run never starts or stops the database; `db-up` and `db-down` do (local trust-auth socket cluster, no secret; a worker may run them, P5-22). No step reads database credentials. When `DATABASE_URL` is set, the OWNER runs every step.

## Prerequisites

All are separate implement-step tasks with their own ledgers. 0005 Solve/RED starts after P1 to P5 are GREEN and TESTED.

| ID | Step | State (updated 2026-11-08) |
|---|---|---|
| P1 | Slice 6d GREEN and TEST (ENTRY LINE, DL-130 to DL-134, DL-138, DL-141, DL-142) | **[Verified]** TEST PASS (2026-11-08 update) |
| P2 | Record format v3 (DL-143): one core for every EFFECT stream; record keys only, M8 and M9 untouched (P5-18) | **[Verified]** TEST PASS, GREEN `ca09d361` |
| P3 | Several ENTRY LINES and several EFFECTS per source (D6B-147; today `slice 1 supports one effect`) | **[Verified]** TEST PASS, GREEN `ce190054` |
| P4 | `db.*` transport step: `db.put`, `db.list` on `effect` lines, host module call, row decode with MIGRATE CHAIN on read, `--stored` over rows, List TYPE (Q5-3) | **[Verified]** TEST PASS, GREEN `060a075d`; row shape check P4c: RED done, GREEN running |
| P5 | Module name per source (Q5-6): generated module `Orders`, not `BeamlSpike` | **[Verified]** TEST PASS with P3 |
| P6 | Fate slice with `quarantine` (DL-125): only for N9 | blocked by D036 (M3, M5; M4 answered, DL-152) |

**[Verified]** Local tools seen on 2026-11-07: Elixir 1.18.1 / OTP 27, `phx_new` 1.8.5 archive, Postgres.app 17.11 (`initdb`, `pg_ctl`, `psql`), Docker, cargo. **[Unknown]** Network access for `mix deps.get` (hex.pm).
