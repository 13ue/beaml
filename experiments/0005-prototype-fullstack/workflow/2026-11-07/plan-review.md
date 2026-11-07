# Plan check: EXPERIMENT 0005 (PROTOTYPE: Postgres, BEAML, LiveView)

**Verdict: BLOCK** (two high objections; both have a small resolving change in the PLAN, no code).
Phase: plan check per `skills/implement-step/SKILL.md`. Fresh context, normal check, not a Devil's Advocate.
Inputs: [README](../../README.md), [plan.md](plan.md), [decisions.md](decisions.md), [owner-review.md](owner-review.md), DL-126 to DL-144 and D026 in the [decision log](../../../../wiki/planning/decision-log.md) and [decisions to be made](../../../../wiki/planning/decisions-to-be-made.md).
By: Opus (plan check exp0005) for every line of this file.

## Observed facts (2026-11-07)

- **[Verified]** `main.rs` (6152 lines): `slice 1 supports one effect` at line 1610; `http.post` is the only transport (line 1446); `defmodule BeamlSpike` at line 2674; usage text at line 5598 reads `--stored SNAPSHOT.jsonl` only; line 4841 requires `--stored` for a source with an EFFECT. No `Rejected` in `main.rs` (consistent with P1 GREEN not started; slice 6d plan names `%BeamlSpike.Rejected{reason: r}`).
- **[Verified]** Toolchain: Elixir 1.18.1 / Mix 1.18.1 on OTP 27 (erts 15.2.7, asdf); archives `hex-2.4.1`, `phx_new-1.8.5`; `/Applications/Postgres.app` present, `pg_ctl (PostgreSQL) 17.11 (Postgres.app)`, `initdb`, `psql`, `createdb` on PATH; cargo 1.94.0.
- **[Verified]** hex.pm answers (`HTTP/2 301` on `repo.hex.pm`). The local hex cache holds `phoenix-1.8.5`, `phoenix_live_view` 1.1.x and 1.2.x, `ecto_sql`, `postgrex`, `opentelemetry-1.7.0`, `opentelemetry_api-1.5.0`, `plug_cowboy-2.8.1`, `lazy_html`. The README **[Unknown]** on hex.pm access is resolved.
- **[Verified]** `probe_support/mix.exs` sets `build_path`, `config_path`, `deps_path`, `lockfile` to the 0002 umbrella and pins `plug_cowboy == 2.8.1`, `opentelemetry_api == 1.5.0`, `opentelemetry == 1.7.0`. It has no application callback. `ProbeSupport.Capture` is a GenServer that a host must start; it writes to `Application.fetch_env!(:probe_support, :output)`. The OTel processor with `ProbeSupport.Exporter` is set in the 0002 umbrella `config/config.exs`, not in the dep.

## Objections

### O1 · high · P2 (record format v3) is gated by D026, not only P6

- **Evidence.** D026 trigger: "Before the fate slice starts (M3, M4, M5) and before the record format v3 step (M8, M9). The main agent opens each as its own question." The plan marks only P6 as blocked by D026 and puts P2 second in the order. Its D026 table covers only how 0005 tests avoid M8 and M9, not how P2 does.
- **Consequence.** Either P2 starts and silently passes the OWNER trigger (a parked item decided by the build), or the free run stops at P2 and 0005 waits on an OWNER answer that the plan says it does not need.
- **Resolving change.** In the P2 row and the D026 table: name the trigger. State that P2 under DL-144 builds the form that avoids both (M8: generated code never accepts a failure struct as an input value; M9: the DL-124 block text keeps its current line shape, no new per-record lines). Add "D026 trigger reached at P2 (M8, M9), not decided" to `owner-review.md` under "Blocked, not decided". If P2 cannot avoid either one, mark P2 blocked like P6.
- → By: Opus (plan check exp0005) · class Migrate (OWNER owns D026)

### O2 · high · N8 can pass without a live Postgres read (Q5-4 option B)

- **Evidence.** N8 has one control: the old source passes against the same snapshot. That varies the source, not the data. Under option B the compiler reads only a temp JSONL file written by `mix beaml.stored`. A stale file, a fixture, a wrong database (`proto_dev` against `proto_test`) or a snapshot written once and reused gives the same exit and the same stderr names. N7 `--stored` exit 0 is also true on an empty snapshot.
- **Consequence.** The thesis test ("the build stops against the live rows") passes while nothing proves the rows came from the table in this run.
- **Resolving change.** Add a data-side control to N8: delete the `order-zero` row by SQL, run the same stricter build again through `mix beaml.stored`: exit 0. Also assert the snapshot file did not exist before the step and holds exactly the `records` row ids that a separate `psql` query returns at that moment (compare ids and count, print no values). For N7, assert the snapshot holds the seeded v1 row before the exit-0 check.
- → By: Opus (plan check exp0005) · class Repair (test design inside the team)

### O3 · medium · No row of the new TYPE VERSION ever reaches the table

- **Evidence.** N7 seeds a v1 row and reads it lazily under `order_v2.beaml`; the row stays `version = 1`. No test writes under v2. Also `order_v2.beaml` adds `note: String` to `Order` but `to_order` builds `Order` without `note`; the variant needs that change too, and the plan does not say so.
- **Consequence.** The thesis says the TYPE change travels "from source to table". With the current N-tests the table never sees version 2 and never holds mixed versions; the `put` side of a version change is unproven.
- **Resolving change (smallest test).** N7b: under `order_v2.beaml` submit `order-3` through the page; one new row has `version = 2` and `value.note = ""`; `/orders` lists the v1 row and the v2 row together; N11 columns still unchanged. Record the `to_order` change in the variant diff.
- → By: Opus (plan check exp0005) · class Repair

## Answers to the check questions

**(1) Built without an OWNER answer? Parked items?**
→ Not as written: O1 (P2 meets the D026 trigger)
→ No 0005 default decides M3, M4, M5, M8, M9
⠀⠀↳ N8 avoids M4 and M9
⠀⠀↳ N9 blocked, `quarantine` only
→ `db-up` as an OWNER step stops a free run (see 5)

**(2) Prerequisites P1 to P6.** Order P1 → P2 → P3 → P5 → P4 is buildable (P5 before P4 keeps the db EFFECT output under `Orders`). Missing setup lines (add to the 0005 host section, no new step):
→ Host wiring of `ProbeSupport`: `Capture` child, `ProbeSupport.setup/0`, `:probe_support, :output` per run
→ OTel config in host `config/config.exs`: processor with `ProbeSupport.Exporter` (a path dep does not carry the umbrella config)
→ `plug_cowboy`, OTel pins `==` versions: check they resolve with the Phoenix 1.8.5 deps
→ `lazy_html` (LiveViewTest in 1.8) fetches a precompiled NIF at build: an outside download, record it
→ `Rejected` name: `Orders.Rejected` needs P1 and P5; consistent with slice 6d

**(3) Thesis or CRUD?** N7, N8, N10, N11 go past CRUD. Missing smallest test: N7b in O3 (a v2 write and a mixed read).

**(4) N8 false pass.** Yes, see O2. Resolving test: the data-side control and the snapshot provenance check.

**(5) Local `pg_ctl` cluster.**
→ No secret: trust auth, no password, no env file read
→ No outside reach: `listen_addresses=''`, Unix socket only
→ Note: default socket mode 0777; add `-c unix_socket_permissions=0700`
→ Class Undo: local, reversible (`db-down`, delete `.pgdata`)
→ A worker may run `db-up` and `db-down` under DL-144; keep the OWNER step only when `DATABASE_URL` is set
→ README contradiction: "never starts, stops" a database, but `run.py db-up` starts one; reword to "the test run never starts it"

**(6) owner-review.md.** All seven big Q5 items are listed first. One big default is not flagged:
→ STORED ROW value shape (P4 content): bare DL-105 projection in `value`, `type` = bare TYPE name, no `value_sha256` or v3 core in the row. DL-127 says "every row a record as in the JSONL store today". This is a record format. Add it as Q5-10 (big) with options A projection only, B v3 core in the row.
→ The db call record in the capture stream uses the v3 core from P2; it is covered once P2 exists.

## Decisions

**Repair**
→ BLOCK statt PASS, weil O1 and O2 are high · By: Opus (plan check exp0005)
→ N7b as objection statt only an answer, weil the caller asked for the smallest missing test · By: Opus (plan check exp0005)
→ ProbeSupport wiring as answer (2) statt objection, weil N3 fails loudly, no false pass · By: Opus (plan check exp0005)

**Undo**
→ Probed hex.pm with one HEAD request (read-only) · By: Opus (plan check exp0005)
→ Worker may run `db-up` (proposal, class Undo) · By: Opus (plan check exp0005)

**Migrate (OWNER chooses)**
→ O1: P2 avoids M8 and M9, or P2 waits for D026 · By: Opus (plan check exp0005), decided nothing
→ Q5-10 row value shape: A projection only · B v3 core in the row · By: Opus (plan check exp0005), decided nothing
