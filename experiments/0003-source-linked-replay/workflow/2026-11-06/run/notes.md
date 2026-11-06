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
