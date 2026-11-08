# RED output: slice 6e, several EFFECTS and ENTRY LINES per source

**[Observed]** Solve/RED phase, 2026-11-07. Full log: [red-output.log](red-output.log). Mapping: [red-plan.md](red-plan.md).
By: Opus (RED multi-effect) for every finding in this file.

## Command

```
git archive 545dded0 experiments/0001-syntax-to-beam | tar -x -C <scratch>/head2
cargo build --offline --quiet --manifest-path <scratch>/head2/experiments/0001-syntax-to-beam/Cargo.toml --target-dir <scratch>/head2/target
BEAML_SPIKE=<scratch>/head2/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_multi_test.py
```

Toolchain: Elixir 1.18.1 (OTP 27), Python 3.13.12, cargo 1.94.0. HEAD moved from 8cae7721 to 545dded0 during RED (6d TEST repair, +24 lines in `main.rs`). The final run uses 545dded0; the 8cae7721 run gave the same 17 failures and 3 passes.

## Result: 14 tests, 17 failures (11 tests red), 3 guards green, exit 1

| Test | Result | Reason today |
|---|---|---|
| N1 | FAIL | exit 1, `slice 1 supports one effect` (the first RED) |
| N2, N3 to N6, N7, N8, N9 | FAIL (6 tests) | setup: the multi source does not build, `slice 1 supports one effect` |
| N10 `two_effects_in_one_pipe` | FAIL | `slice 1 supports one effect`, not the Q6E-4 text |
| N10 `same_entry_operation` | FAIL | the D6B-147 text, not `duplicate name: ui_place` |
| N10 `enum` | FAIL | exit 0: no reserved-name check |
| N11, N11b | FAIL | fmt exit 1, `slice 1 supports one effect` |
| N14 (4 subtests) | FAIL | exit 0, but `defmodule BeamlSpike do`, not `Orders` / `Echo` / `Count` |
| N15 (2 subtests) | FAIL | exit 0, `BeamlSpike` instead of `OrderFlow` / `V2Orders` |
| N13, N14b, N14c | ok | guards (before and after) |

Every failure names a missing feature: the one-EFFECT limit, the one-ENTRY-LINE limit, the stem module name, or a missing check. No import, setup or typo failure.

## Challenge: could the tests pass falsely or fail wrongly?

- **[Observed]** Scratch probe = HEAD with only the two limit checks removed (not in the repository). It builds the fixture with 15 `defmodule` lines: `Replay`, `Http`, `BeamlFailure`, `PaymentError`, `StockError` two times each. N1 counts and N2 catch that. It also compiles `two_effects_in_one_pipe` and `same_entry_operation` with exit 0. So N1 and N10 need real GREEN work; a pure lift of the limits does not pass them.
- **[Observed]** The HEAD output of the hold half (one EFFECT, one ENTRY LINE) passes `elixirc --warnings-as-errors` with exit 0 but warns: `__beaml_from_Amount/1` is defined two times (input PlaceOrder and output Hold share Amount, the G6D limit). N2 checks the warning text, so exit 0 alone cannot pass it.
- **[Observed]** Harness check at HEAD on the two one-EFFECT halves (as `BeamlSpike`, scratch only): `N3_hold_value`, `N3_hold_spans`, `N3_hold_requests`, `N6_hold_reject`, `Q6E2_rejected_shape`, `N3_place_*`, the trace-id stub, `entry/2` and `run/3` with the decoded PlaceOrder: all PASS. So the expected values and stubs are right for one flow.
- **[Observed]** `--stored` expectations at HEAD with records of the halves: the `stock.reserve` orphan block (count 1, line 2); the two-block case (counts 1 and 2); the `ui.hold` ENTRY block after `retire stock.reserve`; both RETIRE LINES exit 0 without DEAD LINE; two W1 lines; W2 for `migrate Payment v1 -> v2` without a Payment record and none with one old record. All as the test expects.
- **[Observed]** The plan's W2 case on Hold is impossible: `error: effect stock.reserve: the constructor field Hold.amount cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)`. The test uses Payment (red-plan.md, Repair).
- **[Inference]** N7 to N9 pin existing per-operation behaviour (D6B-206). They are red only because their records come from the multi build. After GREEN they guard the multi snapshot.
- **[Unknown]** N4, N5 multi-flow cases (`run/4` clauses, `entry/2` dispatch) and N7's `2 entries, 2 checked` cannot be checked before GREEN.

## Impact on existing tests (for GREEN and TEST)

- `tests/redteam_c3_test.py` C4 fails until `run.py` lists `slice6_multi_test.py` (this phase may not edit `run.py`).
- `tests/slice6_entry_test.py` needs the plan table changes (`BeamlSpike` → `Orders`/`Echo`/`Count`, `two_entries` case removed).
- `tests/record_v3_test.py` V18 compiles every `slice*/*.beaml` against the P2 base: equal while P2 is the only change; after P3 GREEN the ENTRY LINE sources differ (module rename).
- Both N13 guards skip every `slice6/multi/` file (each has an ENTRY LINE).

## Limits

- `BASE` = 545dded0, the HEAD at RED end. P2 has not landed. After P2 GREEN `BASE` moves to the P2 pin commit (RV3-14, D6B-212).
- fmt column spacing comes from the scratch probe, because HEAD fmt validates and stops at the one-EFFECT limit. It equals a hand calculation from `aligned`.
