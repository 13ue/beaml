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

## GREEN

Change: `experiments/0001-syntax-to-beam/src/main.rs` (sha256 `2dee707fd1444156f91b53773ad11e8250a583064f94ce3d6459baaff9227b01`, +12 −7). Base: `80de51ea`. Full output: [green-output.log](green-output.log).

- `emit()` always puts the struct modules of the record failure TYPES that no EFFECT names at the top of `BeamlSpike`. Without an EFFECT this is every struct, as before.
- `emit_effect()` puts only the struct modules of the EFFECT failure TYPES after the clauses, as before.
- New helper `effect_failure(name)`. `emit_structs` takes a filter.

### Results

- **[Observed]** `slice6_struct_order_test.py`: 2 tests, OK (RED: 1 FAIL).
- **[Observed]** int 16 OK, failure 22 OK, enum 20 OK, pipe 12 OK, decode 10 OK.
- **[Observed]** constructor 24/25 (`test_constructor_type_in_an_effect_output_field` FAIL), decode_ctor 0/7. Both unchanged, by design until step 8 GREEN.
- **[Observed]** stored_types 33, slice3_types 69, slice4_retire 87, slice5_syntax 60, slice5_squash 24, slice5_rewrite 5: all OK.
- **[Observed]** `cargo fmt --check` exit 0, `cargo clippy --offline --all-targets -- -D warnings` exit 0, `cargo test --offline --no-fail-fast` 17 + 14 passed.
- **[Observed]** The orders guard hashes and the payments snapshot stay equal (guard test PASS). `run.py` was not run. No commit.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| G1 | Repair | Split by EFFECT: the structs that no EFFECT names go to the top; the EFFECT failure structs stay after the clauses. | Move all structs to the top | All structs at the top change the orders outputs (`PaymentError` moves). The guards forbid that. |
| G2 | Undo | A filter argument on `emit_structs` and one helper `effect_failure`. | Two struct lists or a new emit function | Smallest diff. One loop for both places. |
| G3 | Repair | Accept a known limit: a pure clause that builds an EFFECT failure struct (for example `PaymentError { reason: "x" }`) still gets the struct after its use. A `ponytail:` comment in `emit()` records it. | Detect record literals in clause bodies | No fixture or test has this case. The fix needs a body scan or a byte change of the orders outputs. Open point P2. |

By: Opus (GREEN, slice6b-struct-order)

### Open points

- **P2 [Inference, Repair]** G3 limit. The smallest next test: the probe with a pure fn `! PaymentError` that returns `PaymentError { reason: "x" }`, through `elixirc`. A fix then moves that struct to the top and changes no guarded output only if no guarded fixture has such a clause.
- P1 is closed by G1: the guards PASS because the orders fixtures name `PaymentError` only through the EFFECT.
