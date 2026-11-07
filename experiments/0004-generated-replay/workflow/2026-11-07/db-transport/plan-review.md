# Plan check: DB TRANSPORTS and `--stored` over STORED ROWS (EXPERIMENT 0005 P4)

**[Observed]** 2026-11-07, plan check per `skills/implement-step/SKILL.md`. Fresh context, normal check (not a Devil's Advocate). Read only. Checked together with the [multi-effect plan check](../multi-effect-module/plan-review.md), because both plans must fit each other and [the 0005 plan](../../../../0005-prototype-fullstack/workflow/2026-11-07/plan.md).
Target: [plan.md](plan.md), [decisions.md](decisions.md). Also read: the 0005 plan (incl. "Plan repair"), its decisions and [owner-review.md](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md); the [record format v3 plan](../record-format-v3/plan.md) with its [plan-review](../record-format-v3/plan-review.md) and the uncommitted "Plan repair" section; DL-127 to DL-144; D026 and the [red team report](../red-team-01/report.md) (M3, M4, M5, M8, M9, finding D2).
By: Opus (plan check P3/P4) for every finding and decision in this file.

## Verdict: BLOCK

Three high objections (O1, O2, O3). Two medium notes. The fixes are plan-text changes and one fake-stub rule. No design restart.

## Checked and holding

- **[Verified] QDB-5 against DL-143 and Q5-10.** One outbound stream `"responses"` with the v3 core plus `request` is the DL-143 shape. The ROW CORE in the table (Q5-10 B) and the db call record in the stream are two copies. Each one is consistent.
- **[Verified] QDB-7 against Q5-4 B and N8b/N8c.** `mix beaml.stored` writes a new directory per build with `rows.jsonl` and `snapshot-meta.json`. Each row has `row_id`, so N8c can compare the ids with `psql`. The compiler reads only `row_count` (PDB-22), so a partial snapshot does not pass.
- **[Verified] QDB-2.** put/3 is flagged big and named as a change of the 0005 put/4. See note M-b for the stale texts.
- **[Verified] The `[T]` decode per item.** A list item is a ROW TYPE (plain record, PDB-05). Its fields may hold a constructor TYPE (`Amount`). The live list decodes each row through `__beaml_row_<t>`, which has the DL-101 tail (PDB-15, PDB-09). N6 pins `"constructor"` for a row from `list_orders`. N25 pins the constructor per item in `--stored`. Gap: see note M-a.
- **[Verified] Order.** P4a and P4b move no pin site (N13 against the P4 base commit; GREEN stops on a byte change). Under the defaults no step re-pins twice: only P2 moves the pins.
- **[Verified] D026 M3, M5, M8, M9.** No redacted ROW field (M3, checked out). No `retire` for rows (M5). No failure struct as input (M8). The rows count line is its own stream line, with no per-record lines (M9). For M4 see O3.

## Objections

### O1 · high · The plan pins names that P2, P3 and P5 already decided in another way

- **Outcome names (P2).** The record-v3 plan writes `outcome` `"accepted"`/`"rejected"` with `reason` `"status"`, `"decode"` or `"constructor"` in every RESPONSE RECORD. Its `--stored` reader stops on any other value: `stored RESPONSE RECORD has no capture outcome accepted or rejected (DL-138)` (record-v3 Change 3).
- QDB-6 A writes `"ok"`/`"failed"` into the same `"responses"` stream (QDB-5) and into every ROW CORE (PDB-14). PDB-01 says "P2 names win", but PDB-14, N2, N10, N11, N25 and owner-review QDB-6 still pin `ok`/`failed`.
- The QDB-6 A reason ("rejected" means a refused input only) does not hold after P2, because P2 uses `rejected` for outbound failures too.
- **Transport record (P2).** The v3 http writer writes no record on a transport failure. QDB-5 writes one (`value: null`, `reason: "transport"`). The two transports then replay one stream differently (`missing_response` against a recorded failure).
- **Module (P5, Q6E-1 C).** `slice6/db/orders.beaml` and all its variants have no ENTRY LINE. So their module is `BeamlSpike`. But N2 to N11 call `Orders.save`, `%Orders.StoreError{}`, `%Orders.Amount{}` and `Orders.Replay.run`.
- **Replay (P3, Q6E-3 A, D6B-199).** The fixture has three EFFECTS, so P3 gives `Replay.run(operation, a0, trace_id, records)`. N11 calls `run/3`. PDB-19 and QDB-5 say "P3 selects by `trace_id` and `operation`", but D6B-199 keeps `select/2` by `trace_id` only. With one EFFECT per flow (Q6E-4 A) that is enough.
- **Consequence.** N25 and every db call record in `responses.jsonl` stop at the DL-138 outcome error. N2 to N11 fail at an undefined module. The RED then fails for the wrong reason. Or a worker widens the v3 reader to accept `ok`/`failed`: two outcome vocabularies in one stream, against DL-143.
- **Resolving change.**
  - Close QDB-6 into P2: `"accepted"` with `reason: null`; `"rejected"` with `reason` `"transport"`, `"decode"`, `"constructor"` or `"not_found"` (DL-141: "a later reason needs no format change"). A ROW CORE has `outcome: "accepted"`. Change PDB-14, N2, N10, N11, N25 and owner-review QDB-6.
  - The transport-failure record is a big record-format default. Either drop it (as for http) or keep it and flag it big in owner-review.
  - Give the db fixture an ENTRY LINE so that the stem rule gives `Orders`, as in 0005. Or name `BeamlSpike` in the tests.
  - Give the variants the stem `orders` in their own directories (multi-effect O1).
  - N11 uses `run(operation, ...)`. Delete "select by operation" from PDB-19 and QDB-5.

### O2 · high · The fake `BeamlDb` hides a `null` encoding that Postgrex changes (false pass)

- **Evidence.** **[Observed]** OTP 27 `:json.encode(%{a: :null, b: nil})` gives `{"a":null,"b":"nil"}`. Jason (the Postgrex `jsonb` encoder, from `app/_build/dev/lib/jason`) gives `{"b":null,"a":"null"}`. The generated records use `:null` (record-v3 V4: `reason == :null`).
- The fake stores `:json.decode(:json.encode(core))` (PDB-10, PDB-11). So the fake keeps `reason` a JSON null. The real `BeamlDb` gets the core "with atom keys" and passes it to `jsonb`. Then the row gets `"reason": "null"`, a String.
- PDB-14 writes `reason: nil`. `:json` encodes that as `"nil"`. So the fake and the real store differ in both spellings.
- **Consequence.** P4 N2 passes on the fake while every live row in the BEAML-owned table holds a wrong `reason`. Neither the row decode nor the digest reads `reason`, so nothing fails. `mix beaml.stored` then copies the String into `rows.jsonl`. No test ties the fake to the real contract: the 0005 N2 repair checks `value.value` and `value_sha256` only.
- **Resolving change.** Give one encoder to BEAML: the generated code passes `BeamlDb.put` a JSON binary (`:json.encode(core)`), and the host stores it as `$n::jsonb`. The fake stores `:json.decode` of the same binary.
- Add one tie test in 0005 (after N2): `jsonb_typeof(value->'reason') = 'null'`. Also assert that the key set and the JSON types of the stored core equal the P4 N2 expectation. This is the one test that ties the stub to the real contract.

### O3 · high · PDB-09 decides parked M4 for rows, and N18 pins the help line

- **Evidence.** D026 M4 (parked by the OWNER) has option B: "lift D6B-39 as the first slice 6c step before any FATE OPERATION". D6B-39 is the ban on a constructor or enum field in a TYPE with a MIGRATE CHAIN. PDB-09 lifts it for ROW TYPES, as a Repair, by Opus, and it is not in owner-review.md.
- N18 asserts "the constructor text above" exactly, with `help: declare the fate of these rows in a MIGRATE STEP to a new TYPE VERSION of Order`. The 0005 plan says "no assertion on the help line (M4)". Red team D2 calls this help an agent trap: no fate form exists, so the help names an exit that the compiler cannot give.
- **Consequence.** The OWNER walk-through does not see a decision on a parked item. The trap help is pinned by an exact-text test.
- **Resolving change.** Two options (Migrate, the main agent or the OWNER chooses):
  - (a) Keep PDB-09 as the smallest form that 0005 N7 needs. Reclass it Migrate (default, open), flag it big, and list it under "Parked items touched" in owner-review.md and in the D026 table. N18 asserts the exit, the TYPE, field and constructor names and the absent values, but not the help line.
  - (b) Keep D6B-39. Mark 0005 N7 and N7b `blocked: D026 M4`, as N9 is.

## Medium notes (not blocking)

- **M-a · untested list-item literal path.** PDB-18 (`items.0.channel`) commits the `--stored` reader to indexed names, but N25 tests only a constructor. Add the case of an `orders.list` record with item `channel "app"` under `no_app.beaml`: exit 1. Add the control of item `"tv"` with `unknown_fields ["items.0.channel"]`: exit 0. Without it, a reader that skips list items for literals passes. Also flag PDB-18 and the PDB-24 count line big (record format, as QV3-7).
- **M-b · stale put/4.** The 0005 plan ("P4 content", "lib/proto/beaml_db.ex") and owner-review Q5-8 still name `BeamlDb.put/4`. Add a repair line that points to QDB-2.

## Decisions

**Repair**
→ O1 high statt medium, weil every db record stops at the reader. → By: Opus (plan check P3/P4)
→ O1 fix: P2 outcome names statt `ok`/`failed`, weil PDB-01 says so. → By: Opus (plan check P3/P4)
→ O2 high statt medium, weil it gives a false pass on live rows. → By: Opus (plan check P3/P4)
→ O2 fix: one encoder statt a smarter fake, weil it removes the gap. → By: Opus (plan check P3/P4)
→ O3 high statt medium, weil it is an unflagged parked decision. → By: Opus (plan check P3/P4)
→ `[T]` per-item constructor decode accepted, weil N6 and N25 pin it. → By: Opus (plan check P3/P4)

**Migrate**
→ O3: (a) keep PDB-09 flagged big, or (b) N7/N7b blocked by M4. Main agent or OWNER chooses. → By: Opus (plan check P3/P4)
→ O1: drop or keep the transport-failure record (big). Main agent or OWNER chooses. → By: Opus (plan check P3/P4)

**Undo**
→ M-a and M-b medium, not blocking. → By: Opus (plan check P3/P4)
→ Map key order after `jsonb` dropped as low (small maps sort). → By: Opus (plan check P3/P4)
