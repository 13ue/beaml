# Plan check: EXPERIMENT 0005 (PROTOTYPE: Postgres, BEAML, LiveView)

**Verdict: BLOCK** (two high objections; both have a small resolving change in the PLAN, no code).
Phase: plan check per `skills/implement-step/SKILL.md`. Fresh context, normal check, not a Devil's Advocate.
Inputs: [README](../../README.md), [plan.md](plan.md), [decisions.md](decisions.md), [owner-review.md](owner-review.md), DL-126 to DL-144 and D036 in the [decision log](../../../../wiki/planning/decision-log.md) and [decisions to be made](../../../../wiki/planning/decisions-to-be-made.md).
By: Opus (plan check exp0005) for every line of this file.

## Observed facts (2026-11-07)

- **[Verified]** `main.rs` (6152 lines): `slice 1 supports one effect` at line 1610; `http.post` is the only transport (line 1446); `defmodule BeamlSpike` at line 2674; usage text at line 5598 reads `--stored SNAPSHOT.jsonl` only; line 4841 requires `--stored` for a source with an EFFECT. No `Rejected` in `main.rs` (consistent with P1 GREEN not started; slice 6d plan names `%BeamlSpike.Rejected{reason: r}`).
- **[Verified]** Toolchain: Elixir 1.18.1 / Mix 1.18.1 on OTP 27 (erts 15.2.7, asdf); archives `hex-2.4.1`, `phx_new-1.8.5`; `/Applications/Postgres.app` present, `pg_ctl (PostgreSQL) 17.11 (Postgres.app)`, `initdb`, `psql`, `createdb` on PATH; cargo 1.94.0.
- **[Verified]** hex.pm answers (`HTTP/2 301` on `repo.hex.pm`). The local hex cache holds `phoenix-1.8.5`, `phoenix_live_view` 1.1.x and 1.2.x, `ecto_sql`, `postgrex`, `opentelemetry-1.7.0`, `opentelemetry_api-1.5.0`, `plug_cowboy-2.8.1`, `lazy_html`. The README **[Unknown]** on hex.pm access is resolved.
- **[Verified]** `probe_support/mix.exs` sets `build_path`, `config_path`, `deps_path`, `lockfile` to the 0002 umbrella and pins `plug_cowboy == 2.8.1`, `opentelemetry_api == 1.5.0`, `opentelemetry == 1.7.0`. It has no application callback. `ProbeSupport.Capture` is a GenServer that a host must start; it writes to `Application.fetch_env!(:probe_support, :output)`. The OTel processor with `ProbeSupport.Exporter` is set in the 0002 umbrella `config/config.exs`, not in the dep.

## Objections

### O1 · high · P2 (record format v3) is gated by D036, not only P6

- **Evidence.** D036 trigger: "Before the fate slice starts (M3, M4, M5) and before the record format v3 step (M8, M9). The main agent opens each as its own question." The plan marks only P6 as blocked by D036 and puts P2 second in the order. Its D036 table covers only how 0005 tests avoid M8 and M9, not how P2 does.
- **Consequence.** Either P2 starts and silently passes the OWNER trigger (a parked item decided by the build), or the free run stops at P2 and 0005 waits on an OWNER answer that the plan says it does not need.
- **Resolving change.** In the P2 row and the D036 table: name the trigger. State that P2 under DL-144 builds the form that avoids both (M8: generated code never accepts a failure struct as an input value; M9: the DL-124 block text keeps its current line shape, no new per-record lines). Add "D036 trigger reached at P2 (M8, M9), not decided" to `owner-review.md` under "Blocked, not decided". If P2 cannot avoid either one, mark P2 blocked like P6.
- → By: Opus (plan check exp0005) · class Migrate (OWNER owns D036)

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
→ Not as written: O1 (P2 meets the D036 trigger)
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
→ O1: P2 avoids M8 and M9, or P2 waits for D036 · By: Opus (plan check exp0005), decided nothing
→ Q5-10 row value shape: A projection only · B v3 core in the row · By: Opus (plan check exp0005), decided nothing

## Re-check after plan repair (2026-11-07)

**Verdict: PASS** (O1, O2, O3 closed; two medium notes, no block).
Phase: one re-check round of the plan repair (plan.md "Plan repair (after plan check), 2026-11-07", decisions.md Q5-10 and P5-18 to P5-25, owner-review.md). Fresh context, new evidence only.
By: Opus (plan re-check exp0005) for every line of this section.

### Evidence read

- **[Verified]** M8 and M9 option texts, [red team report](../../../0004-generated-replay/workflow/2026-11-07/red-team-01/report.md) lines 148 and 149: M8 is whether a failure struct is accepted as an input value of its TYPE (B4, the host value rule); M9 is whether a build block prints per-record lines or caps them (B6, DL-032 against DL-124).
- **[Verified]** DL-144 Effect: "a step that needs one of them builds the smallest form that avoids it or marks the test as blocked". D036 trigger: the main agent opens M8 and M9 before the record format v3 step.
- **[Verified]** DL-127 option J: "every row a record as in the JSONL store today". DL-143 Effect: "The database stream gets the format from the start." DL-144 lifts the DL-139 record-format limit for 0005 and wants such defaults marked big.

### Answers

**(1) O1 closed.**
→ M8 is a decode rule for fn inputs
→ M9 is a line count in block text
→ Record keys touch neither one
→ Stop rule for a P2 worker: present (P5-18)
→ Avoidance matches DL-144; listed in owner-review.md
⠀⠀↳ The D036 question itself is still open

**(2) O2 closed.**
→ New file per build: no reused file
→ Ids and count equal a fresh `psql` read
→ N8b changes the data, the exit follows
⠀⠀↳ A stale copy cannot follow the delete
→ Remaining gap: see medium M-b

**(3) O3 closed.**
→ N7b writes a version-2 row through the page
→ The list shows the v1 and v2 rows together
→ `to_order` change named in the variant diff
→ Path gap after Q5-10: see medium M-a

**(4) Q5-10 default B.**
→ Consistent with DL-127 J and DL-143
→ Listed under "Big" in owner-review.md, with `By: Fable (default, open)`

**(5) Parked items.**
→ No new default decides M3, M4, M5, M8 or M9
→ The `redacted` core key comes from DL-143, not from M3

### Notes (medium, not blocking)

**M-a · medium · Row paths in N4, N6, N7, N7b do not follow Q5-10 B.**
- Evidence: the repair changes only the N2 expectation to `value.value`. N7b asserts `value.note = ""`; N7 seeds a v1 row by SQL in an unnamed shape; N4 says "stored as `"tv"`". Under B the projection is at `value.value`, and the seed must be a v3 core.
- Consequence: the RED worker must guess the paths; a wrong path fails loudly (no false pass).
- Resolving change: state in RED that every row assertion and the N7 seed use the v3 core shape (`value.value.note`, `value.value.channel`).
- → By: Opus (plan re-check exp0005) · class Repair

**M-b · medium · N8c does not bind the snapshot database to the database of the submit.**
- Evidence: N8c compares the snapshot with a `psql` read, and N8b deletes by SQL, but the plan does not name the database for each. Only N7 asserts its own row id is in the snapshot. A leftover `order-zero` row in `proto_dev` from an earlier run, with the page writing to `proto_test`, passes N8, N8b and N8c.
- Consequence: the live read is proven, but not that the row from this run's submit caused the block.
- Resolving change: N8 asserts the row id of this run's `order-zero` submit is in the N8 snapshot. `snapshot-meta.json` database name equals the Repo database of the submit step. The run starts with an empty `records` table.
- → By: Opus (plan re-check exp0005) · class Repair

### Decisions

**Repair**
→ PASS statt BLOCK, weil O1 to O3 are closed and both notes are medium · By: Opus (plan re-check exp0005)
→ M-b as medium statt high, weil the live read is proven and N2 proves the page write · By: Opus (plan re-check exp0005)
→ M-a as medium statt high, weil a wrong path fails loudly · By: Opus (plan re-check exp0005)

**Undo**
→ Read only; no file changed except this section · By: Opus (plan re-check exp0005)

**Migrate (OWNER chooses)**
→ D036 M8 and M9 stay open; P2 avoids them under DL-144 · By: Opus (plan re-check exp0005), decided nothing
