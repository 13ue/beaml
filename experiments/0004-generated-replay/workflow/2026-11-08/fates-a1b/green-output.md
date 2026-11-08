# GREEN output: fates-a1b

**[Verified]** GREEN run, 2026-11-08, base RED commit `1e0e08df`. By: Opus (GREEN fates-a1b). No commit.
Inputs: [plan.md](plan.md) with "Repairs", [plan-review.md](plan-review.md), [red-plan.md](red-plan.md),
[red-output.md](red-output.md), [red-review.md](red-review.md); DL-166, DL-172, DL-158.

## Changes

| File | Change |
|---|---|
| `experiments/0001-syntax-to-beam/src/main.rs` | `renamed_onto`, its two calls and the QM4-1 A text deleted (DL-166). New `stored_key(ty, version, field)`: steps with `from >= version`, newest first, changes in reverse, each `Rename(old, new)` with `new == name` sets `name = old`. `value_checks` reads the enum and constructor fields and `kept` through it; error texts and fate lookup keep the newest name. `failing_param` replaced by `tested_params` (the parameters with a literal in the first matching clause): one mirror for help and lift (PB-04). `ctor_fate(ctor, tested)` lifts only a `quarantine p` with `p` in `tested` (DL-172, QB-1 either). Empty `tested` (QB-2): no lift, help `no fate line covers a failed rule that tests no parameter with a literal (QB-2 open); …`. PF-11 "has two" error deleted; RF-04 "two fate lines name the field" stays. |
| `tests/slice6_decode_ctor_test.py` | new helper `help_no_literal(ctor)` beside `help_quarantine` |
| `tests/record_v3_test.py` | `HELP_REPIN` lines for `stored-elixir/order`, `nested-fail`, `pipe-fail` move to `help_no_literal("Amount")` (O1 pin move); `decode-ctor/stored-fail` stays |
| `tests/slice6_stored_elixir_test.py` | `CTOR_FAILS` help moves to `help_no_literal("Amount")` |
| `slice6/db/bad_rename/*.beaml` | header comment only: builds (DL-166), path kept (PB-06) |
| `experiments/0005-prototype-fullstack/app/beaml/variants/rename_channel/orders.beaml` (new) | Order v2 `source: Channel`, `migrate Order v1 -> v2 { rename channel -> source }`, `to_order` writes `source: channel` |
| `experiments/0005-prototype-fullstack/run.py` | step `n14` after `n7_seed`: `gen("rename_channel", write=False)`; pass when exit 0 and stderr is exactly `rows: 2 rows, 2 checked, 0 not decodable`; writes the N14 start/finish events to `<run>/use-cases.jsonl`; N14 in `EXPECTED` |

Other `help_quarantine` uses checked: `record_v3_test.py` 171 and 270, `slice6_decode_ctor_test.py` 234 (clause `_, ""`,
tests `currency`): unchanged and passing. RED tests unchanged.

## Commands and results

| Command | Result |
|---|---|
| `cargo build --release`, `cargo build` (0001) | pass |
| `cargo test` | pass (22 + 14) |
| `cargo clippy --all-targets -- -D warnings` | pass |
| `cargo fmt --check` | pass |
| `python3 -B tests/slice6_m4_test.py` | 16 tests OK (RED: 14 failed) |
| `python3 -B tests/slice6_fates_test.py` | 36 tests OK (RED: 5 failed) |
| `python3 experiments/0004-generated-replay/run.py` | pass, 40/40 steps, 780 tests; `results/20261108T115656288117Z` |
| `python3 -B run.py db-up` (0005) | pass; `results/20261108T120704662050Z` |
| `python3 -B run.py run` (0005) | pass, 19 steps, use cases 22 pass + 1 blocked (N9), N14 pass, acceptance empty; `results/20261108T121420978334Z` |

Byte pins: the six sites (EFFECT_OUTPUTS, BYTE_GUARD, byte-guard.json; PIN, entry/multi BASE, P4_BASE) did not move;
their tests pass inside the 0004 run, and no pin file changed. `lib/generated/orders.ex` unchanged (`written: false`
for `gen-rename_channel`). No failed run in this phase.

## Limits

- R3 (db.list items at the newest version), R4 (renames inside a constructor TYPE): excluded, untested.
- Within-step rename order (RED review O1, medium) is implemented in reverse order but not yet tested: TEST phase.
- QB-1, QB-2 stay open for the OWNER; the built defaults are interim.

## Decisions

**Undo**
→ Entry-record checks (`ENTRY RECORDS`, newest version) do not use `stored_key`: the version is the newest, so no rename applies. By: Opus (GREEN fates-a1b)
→ `help_no_literal` lives in `slice6_decode_ctor_test.py` beside `help_quarantine`; the RED constant `NO_LITERAL_HELP` in `slice6_fates_test.py` stays as written. By: Opus (GREEN fates-a1b)
→ A clause that the Rust mirror cannot match gives no lift and the QB-2 help (it was the first-parameter fallback). By: Opus (GREEN fates-a1b)

**Repair**
→ N14 as a `run.py` step that writes its own use-case events statt a mix test in phase n7_seed, weil `committed: :truncate` empties the table per test and the plan names a run.py step. Commits us to: run.py owns the N14 check text. By: Opus (GREEN fates-a1b)
→ N14 passes only on the exact count line statt exit 0 alone, weil a warning or a not-decodable row must fail the case. By: Opus (GREEN fates-a1b)
