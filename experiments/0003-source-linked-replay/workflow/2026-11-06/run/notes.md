# Notes: run.py RED (2026-11-06)

**Scope.** Plan and RED only. No production behavior. No commit. Competing proposals were not written; the task asked only for plan and RED.

## Decisions
- Include gate 1 (`cargo test ... payments_cli_emits_checked_authorize_reference`) as the first step. It exists and gate 1 links it. It makes no result dir, so `result_dir` is null.
- Step result dir = first stdout line of the step, when that line is a dir. All four Python gate tests print it first.
- Repair depends on lookup. A failed lookup gives `status: skipped` and `exit_code: null` for repair. Other steps still run.
- Test seam: one env variable `BEAML_0003_RUN_CONFIG` (JSON: `steps`, `results`, `actions`). The test uses stub steps in a temp dir. No release starts and the real `results/` and `.beaml/actions.jsonl` stay unchanged.
- Python 3.9.6 is the local `python3`. The first attempt used `TestCase.enterContext` (3.11+) and gave a setup error. Changed to `tempfile.TemporaryDirectory` + `addCleanup`. That error was not counted as RED.

## RED
- Command: `python3 -B experiments/0003-source-linked-replay/tests/run_test.py` (repo root).
- Tests: `test_all_steps_pass`, `test_failed_lookup_skips_repair_and_runs_later_steps`, `test_failed_independent_step_fails_run`.
- Expected: runner exit 0 / 1 / 1, then order, `--source-run`, result.json and event assertions.
- Actual: `AssertionError: 2 != 0 : not implemented`, `2 != 1`, `2 != 1`. 3 failures, 0 errors. Test run exit 1.
- Reason: stub `run.py` exits 2 with "not implemented". The failure is missing behavior, not setup. See [red-output.log](red-output.log).

## Open
- Toolchain: python version plus step `toolchain.json` files is enough? (Proposal: yes.)
- Per-step timeout: none in the plan; a hung release blocks the run.
- `integrations/zed-beaml/preview.py` showed as untracked during this phase and later went away. Another process changed it. This phase did not touch it.

## RED review repair: O1 (2026-11-06)
- Source: [red-review.md](red-review.md) O1 (high). O2 and O3 (medium) are GREEN review checks, not test changes.
- `plan.md`: step paths now start at the repo root (`experiments/0003-source-linked-replay/tests/...`). Gate 1 keeps `--nocapture`, as in `workflow/2026-11-05/notes.md`, so its stdout is evidence.
- New test `test_default_steps_match_gate_commands`. It runs `run.py --list-steps` without `BEAML_0003_RUN_CONFIG`. It expects JSON `{"steps": [{"name", "command"}]}` with the five names, order and exact argv. The repair argv ends with `--source-run {result_dir:trace-lookup}`. The test checks that the manifest and the four scripts exist. It starts no step.
- GREEN pass rule: all `run_test.py` tests pass. The TEST phase also runs `python3 experiments/0003-source-linked-replay/run.py` once for real. It must exit 0, and the repair step `result.json` `source_run` must equal the lookup step `result_dir` of the same run.
- RED: `python3 -B experiments/0003-source-linked-replay/tests/run_test.py` from repo root. 4 tests, 4 failures, 0 errors, exit 1. Each fails on the stub exit code: `2 != 0` (all pass, default steps), `2 != 1` (two fail cases), "not implemented". See [red-output.log](red-output.log).

## GREEN (2026-11-06)
- Change: `run.py` only (stub to runner). 138 lines. No test, gate code or wiki change.
- `run.py` runs the five default steps serially from the repo root. `--list-steps` prints them as JSON.
- The repair step gets `--source-run <lookup result_dir>`. The runner replaces the token or appends the pair. It skips repair when lookup fails or gives no dir.
- The run dir keeps `<step>.stdout` and `<step>.stderr` for each started step (O2).
- A step that cannot start gets `status: fail`, `exit_code: null` and a runner line in its stderr. Later steps run. `result.json` and the `finish` event stay (O3).
- Event logging catches all errors. Events have no paths.
- Test SHA-256 before and after: `f477226bc24b3acdd6a4e5f6dc1f11fd73d8f00f07a8add04a3e9f312a874f57` (equal).

**Commands (repo root)**
- `python3 -B experiments/0003-source-linked-replay/tests/run_test.py`: 4 tests, OK, exit 0.
- `python3 -m py_compile experiments/0003-source-linked-replay/run.py`: exit 0.
- `python3 experiments/0003-source-linked-replay/run.py`: exit 0, status pass, about 63 s.
- O3 check: scratch config with a missing program for `trace-lookup`. Exit 1. Lookup `fail`, repair `skipped`, later steps `pass`, last event `finish`/`fail`.
- O3 check: action log path not writable. No exception. Exit 1 (expected from the missing program).

**Run dirs**
- Runner: `results/20261106T081942619923Z`.
- trace-lookup: `results/20261106T081944824172Z`.
- trace-lookup-repair: `results/20261106T082004790073Z`. Its `source_run` equals the lookup dir.
- response-capture: `results/20261106T082005025365Z`.
- replay-run: `results/20261106T082023566609Z`.
- compiler-reference: no result dir. Its evidence is `compiler-reference.stdout` in the runner dir.

**Checklist**
- All `run_test.py` tests pass: yes.
- Real run exit 0, five steps `pass`, every exit code 0: yes.
- Repair `source_run` equals lookup `result_dir`: yes.
- O2 stdout per step retained: yes.
- O3 missing program: yes.
- Python 3.9 compatible: yes (local Python 3.9.6).
- Evidence: [green-output.log](green-output.log), [green-result.json](green-result.json).
