---
id: experiment-0005-prototype-fullstack
kind: experiment
status: proposed
updated: 2026-11-07
revision: 2 (PLAN repair after plan check, free run DL-144)
---

# EXPERIMENT 0005 — PROTOTYPE: Postgres, BEAML, LiveView

**[Proposal]** PLAN phase, 2026-11-07, repaired after the plan check ([plan-review.md](workflow/2026-11-07/plan-review.md), [repair](workflow/2026-11-07/plan.md#plan-repair-after-plan-check-2026-11-07)). No code, no run. Plan: [workflow/2026-11-07/plan.md](workflow/2026-11-07/plan.md). Decisions: [decisions.md](workflow/2026-11-07/decisions.md). OWNER walk-through: [owner-review.md](workflow/2026-11-07/owner-review.md).
Binding OWNER decisions: DL-126 to DL-134, DL-137, DL-139, DL-141 to DL-144 in [the decision log](../../wiki/planning/decision-log.md). DL-144 makes this a free run: every open Migrate question has a built default, marked `By: Opus (PLAN exp0005, default, open)`.
By: Opus (PLAN exp0005) for every proposal on this page.

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
- FATE OPERATIONS. N9 is BLOCKED until the fate slice (DL-125); D036 keeps M3, M4, M5 parked before that slice.
- `redact`, `retire` and `redacted` fields (M3, M5 untouched).
- The host passes no failure struct back into generated code (M8 untouched).
- No assertion on the number of record lines in a block text (M9 untouched). No assertion on the DL-102 help wording (M4 untouched).
- HTTP route entries, deploy, releases, auth, real data, any network service. Answer-class: none (DL-144: local only).
- Ecto schemas per TYPE (DL-127 option E).
- JavaScript behaviour in a real browser. The OWNER may open the page by hand; that is not evidence.

## Acceptance criteria

**[Proposal]** One `run.py` run passes N1 to N7, N7b, N8, N8b, N8c and N10 to N13 with exit 0 and retains its result directory. N9 is reported as `blocked` with the reason, never as `pass`. Details: [plan.md](workflow/2026-11-07/plan.md#n-tests).

2026-11-07 (plan repair 2, QDB-8 B): N7 and N7b stay in this line. They run on the String-only ROW TYPE `Note` (v1 → v2 `add tag`), not on `Order`, which has no chain under the built D6B-39. Details: [plan repair 2](workflow/2026-11-07/plan.md#plan-repair-2-after-re-check-2026-11-07). → By: Fable · Repair

## Repeatable command

```
python3 experiments/0005-prototype-fullstack/run.py db-up     # a worker or the OWNER, once per machine start
python3 experiments/0005-prototype-fullstack/run.py           # every run
```

`run.py` builds the 0001 compiler, generates `app/lib/generated/orders.ex`, runs `mix compile --warnings-as-errors`, `mix ecto.migrate`, `mix test`, the `--stored` cases and writes `results/<UTC>/` with commands, toolchain versions, input and output hashes and the actual results. The test run never starts or stops the database; `db-up` and `db-down` do (local trust-auth socket cluster, no secret; a worker may run them, P5-22). No step reads database credentials. When `DATABASE_URL` is set, the OWNER runs every step.

## Prerequisites

All are separate implement-step tasks with their own ledgers. 0005 Solve/RED starts after P1 to P5 are GREEN and TESTED.

| ID | Step | State (2026-11-07) |
|---|---|---|
| P1 | Slice 6d GREEN and TEST (ENTRY LINE, DL-130 to DL-134, DL-138, DL-141, DL-142) | **[Verified]** RED re-check PASS (commit 8ab33d8d); GREEN not started |
| P2 | Record format v3 (DL-143): one core for every EFFECT stream; record keys only, M8 and M9 untouched (P5-18) | not started |
| P3 | Several ENTRY LINES and several EFFECTS per source (D6B-147; today `slice 1 supports one effect`) | not started |
| P4 | `db.*` transport step: `db.put`, `db.list` on `effect` lines, host module call, row decode with MIGRATE CHAIN on read, `--stored` over rows, List TYPE (Q5-3) | not started |
| P5 | Module name per source (Q5-6): generated module `Orders`, not `BeamlSpike` | not started |
| P6 | Fate slice with `quarantine` (DL-125): only for N9 | blocked by D036 (M3, M4, M5) |

**[Verified]** Local tools seen on 2026-11-07: Elixir 1.18.1 / OTP 27, `phx_new` 1.8.5 archive, Postgres.app 17.11 (`initdb`, `pg_ctl`, `psql`), Docker, cargo. **[Unknown]** Network access for `mix deps.get` (hex.pm).
