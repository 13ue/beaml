# Plan: repeatable command for EXPERIMENT 0003

**Task.** Make `python3 experiments/0003-source-linked-replay/run.py` run all gate tests serially. Record one EXPERIMENT RUN.

**Files**
- `experiments/0003-source-linked-replay/run.py`: new runner (today a stub that exits 2).
- `experiments/0003-source-linked-replay/tests/run_test.py`: new fast test with stub steps.
- Read only: the four gate tests, `0002-http-correlation/run.py` (`save`, `event` pattern), `0001-syntax-to-beam/tests/cli.rs`.

**Steps, in this order** (cwd = repo root; paths from the repo root; revised after RED review O1)
1. `compiler-reference`: `cargo test --manifest-path experiments/0001-syntax-to-beam/Cargo.toml --test cli payments_cli_emits_checked_authorize_reference -- --exact --nocapture` (gate 1 command as in `workflow/2026-11-05/notes.md`; it makes no result dir).
2. `trace-lookup`: `python3 -B experiments/0003-source-linked-replay/tests/trace_lookup_test.py`.
3. `trace-lookup-repair`: `python3 -B experiments/0003-source-linked-replay/tests/trace_lookup_repair_test.py --source-run {result_dir:trace-lookup}`. The runner replaces the token with the result dir of step 2 of the same run. Skip it when step 2 fails or gives no dir.
4. `response-capture`: `python3 -B experiments/0003-source-linked-replay/tests/response_capture_test.py`.
5. `replay-run`: `python3 -B experiments/0003-source-linked-replay/tests/replay_run_test.py`.

**First failing test.** `run_test.py::test_all_steps_pass`: stub steps all exit 0, expect runner exit 0, order, `--source-run` = lookup dir, result.json fields, events.

**Default step test (O1).** `run_test.py::test_default_steps_match_gate_commands`: `run.py --list-steps` (no config env) prints JSON `{"steps": [{"name", "command"}]}`. The test compares the five names, order and exact argv lists above, with the token `{result_dir:trace-lookup}` for the repair step. It checks that the manifest and the four scripts exist. It starts no step.

**Minimal change**
- Each gate test prints its result dir as the first stdout line. The runner keeps step stdout/stderr in its own `results/<UTC-id>/` and reads that line.
- `result.json`: `command`, `started_at`, `finished_at`, `toolchain` (python version plus each step `toolchain.json` when present), `steps[]` (`name`, `command`, `exit_code`, `result_dir`, `status`), `status`.
- Exit 0 only when every step exits 0. Else exit 1. Write result.json in `finally`.
- Events `start`, `step` (target = step name, result pass/fail/skipped), `finish`. No paths. Logging never raises.
- `--list-steps`: print the default steps as JSON and exit 0. Run nothing.
- Seam: env `BEAML_0003_RUN_CONFIG` names a JSON file with `steps` (argv per step name), `results` and `actions`. Default: real steps, `results/`, `.beaml/actions.jsonl`.

**Checks.** `python3 -B experiments/0003-source-linked-replay/tests/run_test.py` (GREEN). `python3 -m py_compile` on both files.

**GREEN pass rule (O1).** All `run_test.py` tests pass. In addition, the TEST phase runs `python3 experiments/0003-source-linked-replay/run.py` once for real (slow, starts releases). It passes only when the runner exits 0, `result.json` has `status: pass` and five steps with `status: pass`, and the repair step `result.json` `source_run` equals the `result_dir` of the lookup step of the same run.

**Out of scope.** Changes to gate tests, 0002 code, results, wiki, README. Parallel runs, retries, timeouts per step, input hashes of the whole tree.
