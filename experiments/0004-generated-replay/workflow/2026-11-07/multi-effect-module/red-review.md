# RED review: slice 6e, several EFFECTS and ENTRY LINES per source, module named from the source

**[Observed]** RED review phase, 2026-11-07. Fresh context. Target: commit eb6def2c (`tests/slice6_multi_test.py`, `slice6/multi/`, [red-plan.md](red-plan.md), [red-output.md](red-output.md), [notes.md](notes.md)) against the repaired [plan](plan.md) and [decisions](decisions.md) D6B-197 to D6B-213, Q6E-1 to Q6E-4; DL-131, DL-133, DL-139, DL-144.
By: Opus (RED review multi-effect) for every finding in this file.

## Verdict: PASS

No critical or high objection. Two medium notes for GREEN and the commit after P2 GREEN.

## Run

```
git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>
cargo build --offline --quiet --manifest-path <scratch>/experiments/0001-syntax-to-beam/Cargo.toml --target-dir <scratch>/target
BEAML_SPIKE=<scratch>/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_multi_test.py
```

- **[Observed]** HEAD eb6def2c. `Ran 14 tests`, `FAILED (failures=17)`: 11 tests red, 3 green (N13, N14b, N14c). Equal to red-output.md.
- **[Observed]** Every red names a missing feature: `slice 1 supports one effect` (N1, N2, N3 to N9 setup, N10 pipe case, N11, N11b); the D6B-147 text (N10 same operation); exit 0 without a reserved-name check (N10 `enum`); `defmodule BeamlSpike do` instead of the stem module (N14, N15). No import, setup or typo failure.
- **[Observed]** The working tree holds uncommitted P2 GREEN changes. They were not built or run here.

## Checks per question

1. **RED count.** **[Observed]** 14 tests, 11 red, 3 guards green. Genuine.
2. **Shared parts once, every operation callable.** **[Observed]** N1 counts one of each shared module and one of each `def ui_place(`, `def ui_hold(`, `def payments_authorize(`, `def stock_reserve(`. N2 fails on any elixirc warning (a duplicate def or module warns in Elixir 1.18.1). A `Replay` that drops one operation fails N5: `entry/2` for both ENTRY RECORDS, `run/4` for both operations, the wrong flow on a trace and an unknown operation each give `:operation_mismatch`. N4 pins both live writers (`record` and `entry_record`) by operation. **[Inference]** No false pass from a single shape that keeps one operation.
   - **[Observed]** At HEAD, `Replay.run/3` decodes the recorded body inline (`__beaml_result_<op>`) and calls no transport. N5 does not count stub requests during a REPLAY RUN. Dropped as low: a live call would need new code that the plan does not describe.
3. **Q6E-1 C guards.** **[Observed]** N14b: `slice2/reuse/orders.beaml` (EFFECT, no ENTRY LINE) stays `BeamlSpike`; N13 guards every tracked source without an ENTRY LINE byte for byte. N14c: stem `order-flow` keeps the existing stem error. Probe at HEAD: stems with a digit first or a leading `_` or a capital also get that error, so the module rule only sees lowercase identifier stems. Stems such as `orders_` and `a__b` pass the stem check; their module name is not pinned (low, dropped).
4. **Q6E-4 A.** **[Observed]** The compile error text is pinned exactly (`BAD_CASES`, exit 1, empty stdout). The control (two flows, each with one EFFECT) is the main fixture: N1 exit 0, N3 runs both flows.
5. **The `a0` default.** See M2. **[Observed]** HEAD `run/3` binds `a0` to the flow parameter and calls `to_order` itself, so `a0` = the decoded input continues the existing contract. It is part of Q6E-3 (Migrate, not big). The owner review lists Q6E-3; it does not need a separate big entry.
6. **N13 base and P2.** See M1.
7. **v2 fixtures.** **[Observed]** No. Every `--stored` call uses `stored/empty.jsonl` (0 bytes, not in the P2 converter list) or a snapshot that the test writes from the live records of the build under test. After P2 these records are version 3 by construction. N9 builds one old record from a live record with the unchanged digest rule (QV3-6 A). N7 to N9 use `assertIn`, `assertNotIn` and a `warning: DEAD LINE:` line filter, so the P2 RESPONSE count lines do not break them.

## Objections

**M1 · medium · Two base pins cross between P2 and P3.**
- Evidence: **[Observed]** multi `BASE = "545dded0"`. P2 changes `Replay.record/3` in every EFFECT source, so N13 here goes red by construction after the P2 GREEN commit. RV3-14 in `record_v3_test.py` lists five pin sites; this BASE is a sixth and is not in that list. **[Observed]** `record_v3_test.py` V18 lists `slice*/*.beaml` with a git pathspec, which now matches the 7 `slice6/multi/` files. At P2 they fail equally on both compilers, so V18 passes. After P3 GREEN, V18 fails on them (exit 1 to 0) and on the 3 `slice6/entry` fixtures (the `defmodule` line is a hunk outside the writers). Only red-output.md says so; the plan table of changed assertions does not.
- Consequence: a worker that finds N13 red for a P2 reason may move BASE to a commit after P3 GREEN. Then N13 compares the compiler with itself and passes with no proof.
- Resolving test: the commit after P2 GREEN moves this BASE to the P2 GREEN hash, with the other five sites. P3 GREEN adds V18 to the changed-assertion table: filter ENTRY LINE sources (G6D-01) in V18, or retire V18 after P2 TEST, with a reason. The P3 TEST phase checks that BASE is not a P3 commit.

**M2 · medium · The `a0` default has the wrong class label.**
- Evidence: **[Observed]** red-plan.md records "N5 `a0` = the decoded PlaceOrder" as Repair with `(default, open)`. That marker is the DL-144 form for a Migrate default. The decision is a detail of Q6E-3 (Migrate, not big).
- Consequence: the OWNER walk-through of Q6E-3 does not show the `a0` meaning, and a Migrate detail looks like a Repair.
- Resolving step (docs phase): file the item under Q6E-3 as Migrate, and add a half line to the Q6E-3 line in the 0005 owner review: "`a0` is the flow parameter (decoded input TYPE), as `run/3` today". No test change.

## Decisions

**Repair**
→ PASS statt BLOCK, weil no critical or high objection holds: every red is genuine, and N1, N2, N5 catch a dropped operation. Commits us to: M1 and M2 carried to the P2 commit and the P3 GREEN, TEST and docs phases. → By: Opus (RED review multi-effect) · Repair
→ M1 medium statt high, weil red-output.md and the BASE comment already state both moves; the risk is a coordination slip, not a wrong test. → By: Opus (RED review multi-effect) · Repair

**Undo**
→ `a0` = decoded input not raised to big, because no 0005 host code calls `Replay.run` (Q6E-3 "not big"). → By: Opus (RED review multi-effect) · Undo
→ No request count in N5 dropped as low (inline replay body at HEAD). → By: Opus (RED review multi-effect) · Undo
→ Unpinned stems `orders_`, `a__b` dropped as low. → By: Opus (RED review multi-effect) · Undo
→ P2 working-tree changes not run; review covers HEAD eb6def2c only. → By: Opus (RED review multi-effect) · Undo
