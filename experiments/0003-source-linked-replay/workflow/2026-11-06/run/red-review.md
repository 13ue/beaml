# RED review: run.py of EXPERIMENT 0003 (2026-11-06)

**Mode.** Advocatus diaboli. Spec mode for `plan.md`, code mode for `tests/run_test.py`. Target: commit `0ed0e84`.

**Verdict: PASS WITH CHANGES.** The RED is a genuine behavior RED. One high objection needs a plan change before GREEN.

**Observed.** `python3 -B experiments/0003-source-linked-replay/tests/run_test.py` from repo root: 3 failures, 0 errors, exit 1. All three fail at the runner exit code (`2 != 0` / `2 != 1`, "not implemented"). The later assertions are satisfiable: stub dirs are outside the runner `results`, event keys contain no `/`, Python 3.9 compatible.

## Objections

### O1. high (implementation / spec quality): the real step list has no check

- **Claim.** The fast test exercises only the `BEAML_0003_RUN_CONFIG` seam. No check covers the default steps that `python3 .../run.py` actually runs. `plan.md` "Steps" lists `python3 -B tests/trace_lookup_test.py` etc. with "cwd = repo root". Taken literally, these paths do not exist from the repo root. The plan "Checks" asks for "one real run" but gives no pass criterion.
- **Consequence.** A GREEN with a wrong default (wrong path, missing step, gate 1 filter typo, repair without `--source-run`) passes `run_test.py`. The repair case is a silent false pass: `trace_lookup_repair_test.py` line 106 defaults `--source-run` to the 2026-11-05 baseline. It then checks the old archive, not the fresh lookup run.
- **Smallest fix.** (a) Correct the plan paths to `experiments/0003-source-linked-replay/tests/...`. (b) Add one fast test: load the default config of `run.py` without the env variable, compare the five argv lists with the README gate commands, and check that each script / manifest exists. (c) Make the real GREEN run a gate: runner exit 0, five steps `pass`, and the repair step `result.json` `source_run` equals the lookup step `result_dir`.

### O2. medium (scope): runner-own evidence is not asserted

- **Claim.** README line 48 requires retained command, toolchain versions and hashes per run. The plan keeps step stdout/stderr in the runner dir. The test asserts only `result.json` there. The `compiler-reference` step makes no result dir, so its stdout is its only evidence.
- **Consequence.** A GREEN that discards step logs passes. Gate 1 evidence and the output of a step that fails before it prints its dir are then lost.
- **Smallest fix.** In `test_all_steps_pass`, assert one stdout file per step in the runner dir that contains `stub output <name>`. Optionally add an `output-hashes.json` as in the gate tests.

### O3. medium (risk): failed-run preservation is tested only for a clean non-zero exit

- **Claim.** The plan writes `result.json` in `finally`. No test covers a step that cannot start (missing executable gives `FileNotFoundError`) or a step that exits before it prints its dir.
- **Consequence.** A GREEN that lets the exception escape stops later steps, and can leave no `finish` event. The README "preserve failed runs" holds only partially.
- **Smallest fix.** Add one case: a step argv with a missing executable. Expect exit 1, status `fail` for that step, later steps still run, `result.json` present, last event `finish`/`fail`.

## Deliberately not challenged

- **Per-step timeout.** Not a real risk here. Each gate test bounds its own subprocesses (`timeout=180`, repair `timeout=20`) and the release readiness (20 s deadline). The cargo step is deterministic. Leaving it out of scope is acceptable.
- **`--source-run` lookup dir in the seam.** The test is strong enough: the dir must exist and contain `trace-lookup` in its name, and stubs write outside the runner `results`. A runner that passes its own dir or the latest `results/` entry fails.
- **Toolchain scope.** Python version plus step `toolchain.json` files meets "toolchain versions", because the step dirs are linked.

**Not inspected.** `0002-http-correlation/tests/test_runner.py` in detail, `0001-syntax-to-beam/tests/cli.rs`, the `event` helper of the gate tests.

disposition: O1 applied; O2, O3 recorded as GREEN review checks
disposition_rationale: null

## Disposition (main agent, 2026-11-06)

- **O1 (high): applied.** `plan.md` step paths start at the repo root. New fast test `test_default_steps_match_gate_commands` checks `run.py --list-steps`: five names, order, exact argv and the `--source-run {result_dir:trace-lookup}` token. The GREEN pass rule now includes one real `run.py` run in the TEST phase. It must exit 0, and the repair `source_run` must equal the lookup `result_dir`. RED rerun: 4 tests, 4 failures on the stub exit code.
- **O2 (medium): recorded as a GREEN review check.** The runner dir keeps one stdout file per step.
- **O3 (medium): recorded as a GREEN review check.** A missing program fails only its step. `result.json` and the `finish` event stay.
