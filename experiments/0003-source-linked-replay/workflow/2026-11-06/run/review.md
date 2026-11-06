# GREEN review: run.py of EXPERIMENT 0003 (2026-11-06)

**Mode.** Advocatus diaboli, code mode. Target: commit `f303eb0` (`run.py` GREEN). Read only. `run.py` was not run.

**Inputs.** `run.py`, `tests/run_test.py`, the four gate test `__main__` blocks, `0001-syntax-to-beam/tests/cli.rs`, README line 48 and "Gate status", `plan.md`, `notes.md`, `red-review.md`, `green-result.json`, runner dir `results/20261106T081942619923Z` and its four step dirs.

**Verdict: BLOCK (one high, small fix).** The runner logic is sound. One gate can report pass with zero tests executed.

## Observed

- **Exit code.** Run status is `pass` only when every step has `exit_code == 0` (`run.py:112`, `:121`). Skipped, not started and signalled steps give `fail`. `KeyboardInterrupt` keeps the initial `fail` and `finally` writes `result.json`.
- **Repair source.** The repair argv uses the lookup `result_dir` of the same run, only when lookup passed (`run.py:78-84`). Lookup prints its fresh run dir as the first stdout line (`trace_lookup_test.py:265`). The repair test also asserts `status == pass` in the source run (`trace_lookup_repair_test.py:37`). Real run: repair `source_run` equals lookup `result_dir` (`20261106T081944824172Z`).
- **Failed runs.** The runner and the gate tests never delete a result dir. `results/` is not ignored by git.
- **Events.** `target` is the step name or `experiment-0003`; `result` is a status. No paths. `event()` catches all `Exception`s (`run.py:36-43`).
- **O2.** Each started step has `<step>.stdout` and `<step>.stderr` in the runner dir (`run.py:104-107`). Met in the real run.
- **O3.** A missing program gives `FileNotFoundError`, caught at `run.py:108`. Step `fail`, `exit_code: null`, later steps run, `result.json` and `finish` stay. Met.

## Objections

### O1. high (implementation): gate 1 passes when its test does not exist

- **Claim.** `compiler-reference` is `cargo test ... payments_cli_emits_checked_authorize_reference -- --exact` (`run.py:17-19`). Cargo exits 0 when the filter matches no test ("0 passed; ... filtered out"). `run.py:112` takes exit 0 as `pass`. `run_test.py:118-131` checks the manifest and the four Python scripts, not the Rust test name. A rename, removal or `#[ignore]` of the test in `0001-syntax-to-beam/tests/cli.rs:22` is not detected.
- **Consequence.** `run.py` exits 0 and records the compiler-reference gate as `pass` with no test executed. This is a false pass of a verified gate in the repeatable command.
- **Smallest fix.** For `compiler-reference`, require `1 passed` in the step stdout (the real run has `test result: ok. 1 passed`) or else set `fail`. Alternative: a fast `run_test.py` check that `cli.rs` has `fn payments_cli_emits_checked_authorize_reference` without `#[ignore]`. The stdout check also covers a later filter change.

### O2. medium (scope): the runner dir does not bind the evidence it links

- **Claim.** README line 48 requires command, toolchain versions, hashes and evidence "under a new `results/<UTC-id>/` per run". The runner dir holds `result.json` and step logs only. It has no `output-hashes.json` (`run.py:119`, `:127`). The step dirs are linked by absolute paths (`/Users/lennart/...`, `run.py:67`). The `compiler-reference` stdout is the only evidence of gate 1 and it has no hash.
- **Consequence.** A later edit or removal of a linked step dir, or of the gate 1 stdout, is not detectable from the runner record. In a different checkout the links do not resolve. The red-review O2 named the hash as optional, so this is a disclosed gap, not a regression.
- **Smallest fix.** Write `output-hashes.json` in the runner dir over its own files plus the SHA-256 of each step dir `output-hashes.json` and `result.json`. Store `result_dir` relative to the repo root.

## Deliberately not challenged

- **Step exit 0 without a result dir.** `run.py` does not require a `result_dir` for the four Python steps. Each gate test prints its run dir before any check and exits non-zero on failure, so no current path gives a false pass.
- **Python version.** `toolchain.python` is the runner interpreter, while steps start `python3` from `PATH`. The step `toolchain.json` files record `Python 3.9.6` each, so a mismatch stays visible.
- **No per-step timeout.** Accepted in `plan.md` "Out of scope" and red-review; gate tests bound their own subprocesses.

**Not inspected.** The full bodies of the gate tests, `run_test.py` assertions beyond the default-step check, the parallel TEST run.

disposition: pending
disposition_rationale: null
