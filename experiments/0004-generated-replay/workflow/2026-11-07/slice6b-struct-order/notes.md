# Slice 6b mini-step struct-order: notes

## Solve

- Baseline: commit `cd379ff0`, the scratch `git archive` build of step 8 (`cargo build --offline`). The test runs with `BEAML_SPIKE` set to that binary. Toolchain: cargo 1.94.0, rustc 1.94.0, Elixir 1.18.1 (OTP 27), Python 3.13.12.
- **[Observed]** The RED review probe gives exit 0 from the compiler and exit 1 from `elixirc` (`BeamlSpike.Bad.__struct__/1 is undefined`).
- **[Observed]** Control: `slice2/reuse/orders.beaml` with the same stubs and `elixirc --warnings-as-errors` gives exit 0. So the harness is not the cause.
- **[Observed]** A hand copy of the probe output with `defmodule Bad` moved to the top of `BeamlSpike` compiles with exit 0. So the test can pass after a correct GREEN. The copy stays in the scratch directory.
- **[Observed]** The step 5 guard hashes (baseline `80bd33cd`) are equal to the `cd379ff0` outputs. `payments.beaml` is equal to its snapshot.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| M1 | Undo | Own mini-step and test file `tests/slice6_struct_order_test.py`, before step 8 GREEN. | Fix inside step 8 GREEN | RED review objection 2: the fix needs its own test. |
| M2 | Undo | The probe is the 8-line source of the RED review, inline in the test. | A fixture file | One case, no snapshot. |
| M3 | Undo | `elixirc --warnings-as-errors` compiles the output with the step 7 stubs (`slice6_decode_test.STUBS`). | No stubs | Without stubs, `ProbeSupport` and `:otel_span` give undefined-call warnings. The step 8 runtime uses the same stubs. |
| M4 | Undo | The guards reuse the step 5 constants (`slice6_pipe_test.EFFECT_OUTPUTS`, `PAYMENTS`, `PAYMENTS_SNAPSHOT`). | New hashes | Same values on `cd379ff0`; one source of the hashes. |
| M5 | Undo | The contract does not set where the structs go (top of the module or before the first use). It sets only "before any use" and the byte guards. | Set the place | The GREEN worker picks the smallest change that keeps the guards. |

### Open points

- **P1 [Inference, Repair]** If GREEN moves the structs to the top for every module, the EFFECT fixture outputs stay equal only because they have no failure struct in front today. The guards check this.

## RED

Command (repository root): `BEAML_SPIKE=<scratch>/basecd37/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_struct_order_test.py`. Full output: [red-output.log](red-output.log).
Input (sha256): `tests/slice6_struct_order_test.py` `9c16ba019a00592605e56db370636ee8db70b536a9ee2fba98e553fb15135004`.
Result: 2 tests, 1 FAIL, 1 PASS. Exit 1.

| Test | Expected | Actual today |
|---|---|---|
| `test_effect_module_with_pure_record_failure_compiles` | `elixirc` exit 0 | exit 1: `BeamlSpike.Bad.__struct__/1 is undefined, cannot expand struct BeamlSpike.Bad` |
| `test_effect_fixture_outputs_stay_byte_equal` | the guard values | PASS (guard) |

### RED checks

- The failure is the missing behavior: the compiler gives exit 0; `elixirc` fails on the struct order only.
- `main.rs` was not changed. `run.py` was not run. No result directory was touched. No commit.
