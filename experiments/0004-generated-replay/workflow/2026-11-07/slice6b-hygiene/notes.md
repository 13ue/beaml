# Slice 6b step 0: notes

## Test-first exception

The step changes format and two lint forms only. It adds no behavior, so no test can fail first.
The plan (Step 0, "Check instead of RED") gives the alternative checks. This ledger records them in `before.log`, `after.log` and `test-result.json`.

## Alternative checks

- `capture.py BINARY` records sha256 digests of the compiler output for 129 fixed cases. Run it with the binary from before and after the change. The two logs must be equal byte for byte.
- Compile cases: `example.beaml` (0001), `payments.beaml` (0002), GEN `arms/gen/orders.beaml` with each stored snapshot.
- DIFFLIB cases (DL-067): `--remove-dead` on every `slice4/*` and `slice5/*` fixture, with each stored snapshot, with and without `--assume-complete`. 15 cases write a non-empty diff, so `matching_blocks` runs.
- The parity tests against Python difflib are `tests/slice4_retire_test.py` (`assert_removed`) and `tests/slice5_squash_test.py` (`assert_removed`). Both run in the 0004 `run.py`, before and after.
- The suite counts of the 0004 `run.py` and `cargo test` are equal before and after.

## Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| 1 | Undo | Loop at 3039: `for (i, line) in a.iter().enumerate().take(ahi).skip(alo)` | `a[alo..ahi]` with an index offset | Clippy's own form. Same indexes `alo..ahi`, same order. |
| 2 | Undo | One local `type Recheck<'a>` in the test function | `#[allow(clippy::type_complexity)]` | The plan names a TYPE alias. The alias has test scope only. |
| 3 | Undo | Proxy for "the compiler output of every fixture the 0004 tests use": `capture.py` on fixed fixtures, plus the full suite before and after | Capture the random-name test inputs | The tests make random names without a seed, so their inputs change on each run. |
| 4 | Undo | GEN `orders.beaml` compiles with `--stored` | Compile it without a snapshot | Without `--stored` the compiler refuses the source (exit 1). |
| 5 | Undo | Keep the result directories of the 0001 and 0004 runs, before and after | Delete the failed 0001 run | The repository keeps failed runs. |

## Limits

- `capture.py` stores digests, not the full output. A changed digest shows a change, not its place.
- The 0001 run before the change stops at `compiler-format`. It does not show the clippy and test steps before the change. `cargo test` and clippy ran on their own before the change.
