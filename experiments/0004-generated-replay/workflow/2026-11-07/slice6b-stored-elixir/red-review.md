# RED review: slice 6b step 13, the --stored check through Elixir (DL-121) and the lost ENUM LITERAL block (DL-122, DL-124)

**[Proposal]** RED REVIEW, 2026-11-07. Fresh context, review only. No test edit, no production edit, no commit, no `run.py` run.
Target: `tests/slice6_stored_elixir_test.py` and `slice6/stored-elixir/` at HEAD b0802087.
Read: `skills/implement-step/SKILL.md`, [plan.md](plan.md) (with "Plan repair"), [plan-review.md](plan-review.md), [decisions.md](decisions.md), [spec.md](spec.md), [notes.md](notes.md), [red-output.log](red-output.log), DL-032, DL-102, DL-121, DL-122, DL-124.
By: Opus (RED review, slice6b-stored-elixir) for every judgement in this file.

## Verdict

**PASS.** No critical or high objection. Three medium objections (O1 to O3) are noted for GREEN and the TEST review.
By: Opus (RED review, slice6b-stored-elixir)

## Re-run (observed)

- **[Observed]** Compiler: scratch copy of HEAD b0802087 (`git archive HEAD experiments/0001-syntax-to-beam`), `cargo build --offline`. The uncommitted step 12 GREEN files were not used. The imported helper tests (`slice6_decode_ctor_test.py`, `slice6_decode_test.py`, `slice6_failure_test.py`, `stored_types_test.py`) and the fixtures have no uncommitted change.
- **[Observed]** Command: `BEAML_SPIKE=<scratch>/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_stored_elixir_test.py -v`.
- **[Observed]** Result: 15 tests, 9 FAIL, 6 ok, 1.3 s. The same tests and the same assertion heads as `red-output.log`.
- **[Observed]** FAIL E1, E2, E4, E8, E9a, L1, L1b: exit 0 and Elixir on stdout where exit 1 and the exact text are expected. FAIL E3 event, E5: no `stored-elixir` event. Each FAIL is missing behaviour; no setup, import or fixture error.
- **[Observed]** ok: E3 build, E6, E7, E9b, L2, L3 (guards).
- **[Observed]** `slice6/decode/orders.beaml` holds `Pending = "pending"  ` once, so the L1 and L1b replace changes the source (no false RED from a missed replace).
- **[Observed]** Probe: `elixir -e '# beaml-stored-check\nProcess.sleep(4000)'` is visible to `pgrep -f beaml-stored-check` on this host. The E8 kill check works when the marker is in the argv.

By: Opus (RED review, slice6b-stored-elixir)

## Checks per case

- **E1, E2 (RED).** **[Inference]** Every failing fixture (pipe, nested, rec) fails on a literal `""` clause head of a called fn with the stored value passed directly. A static "follow one pipe step" rule could decide E1 and E2 alone. E4 (no elixir gives the toolchain error for the same input), E3/E5 (event with `calls: 4`) and E8 (time limit) together force a real Elixir run, so a static-only GREEN fails the file. No objection. By: Opus (RED review, slice6b-stored-elixir)
- **E4 (RED).** **[Observed]** `PATH` is an empty scratch directory. A GREEN with an absolute `elixir` path or a fallback path runs Elixir and gives the E1 text, not `NO_ELIXIR`, so E4 fails on it. The event `result: "error"`, `ms: 0` is asserted. No objection. By: Opus (RED review, slice6b-stored-elixir)
- **E5 (RED).** **[Observed]** `calls == 4` is asserted: four records, one `!` Amount call each, PaymentState has no `!` signature. `ms` is only `>= 0` (see O2). By: Opus (RED review, slice6b-stored-elixir)
- **E8 (RED).** **[Observed]** Exact run error text, exit 1, wall time below 12 s, event `error`, and `pgrep -f beaml-stored-check` 1 s after exit. See O1 for the limits. By: Opus (RED review, slice6b-stored-elixir)
- **E9a (RED).** **[Observed]** Fails today for the right reason: line 1 matches only signature 2, whose static body TYPE is `Amount`, so `ctor_fault` gives no fault and the build exits 0. **[Inference]** E9a also guards the observation of the RED worker: line 2 matches the `!`-free signature 1 first. A GREEN that calls `new_Amount_1` for it gets a bare struct, the D6B-122 driver raises `CaseClauseError`, the run error replaces the E1 text and E9a fails. A GREEN that picks signature 2 for line 2 gives count 2 and fails too. By: Opus (RED review, slice6b-stored-elixir)
- **L1, L1b (RED), E7 (guard).** **[Observed]** `LOST_LITERAL` holds no stored String: it names the TYPE VERSION, the field, the enum, the record source line and the help line (DL-124). E7 asserts that L1 and L1b stderr hold neither `pending` nor `wait`, and that E1/E2 stderr and events hold neither `EUR` nor the `trace_id` (DL-032). By: Opus (RED review, slice6b-stored-elixir)
- **L2, L3 (guards).** **[Observed]** `stored.jsonl` line 1 `ok` (current literal) and line 3 `refunded` (in `unknown_fields`) do not block (L2). `stored-resolved.jsonl` line 2 `pending` in `unknown_fields` gives the DL-103 note and no block (L3). DL-103 is covered. By: Opus (RED review, slice6b-stored-elixir)
- **D6B-111 deferred edit.** **[Inference]** The `stored` argument of `run_runtime` only feeds the `--stored` check of the runtime build. The old test never asserted that this build passes with a lost literal; it was the L1 case by accident. The asserted behaviour (the written record gives the DL-103 note, count 1) stays. No coverage is lost. By: Opus (RED review, slice6b-stored-elixir)

## Objections

**O1 · medium · The E8 kill check can pass vacuously, and the default limit has no test.**
Evidence: E8 proves "no leftover process" only through `pgrep -f beaml-stored-check`. Nothing asserts that the marker is in the argv of the running child. A GREEN whose DRIVER has no `# beaml-stored-check` line, or that sends the driver another way, leaves an endless BEAM process and E8 still passes. E8 also sets `BEAML_STORED_ELIXIR_LIMIT_S=2`; no case runs without it.
Consequence: a GREEN that kills only the shell launcher, or that has no limit (or a very high one) when the env value is unset, passes every test. A real build with a looping constructor then hangs or leaks a busy BEAM process: the O1 (high) defect of the plan check.
Resolving test: in E8, assert that `pgrep -f beaml-stored-check` finds a process during the run (for example a second call before the limit), or assert the marker in the generated DRIVER through U1; add a U1 case or a code check that the limit without the env value is 60 s, and one invalid value (`0`, `x`) gives the build error.
By: Opus (RED review, slice6b-stored-elixir)

**O2 · medium · E5 accepts a constant `ms: 0`.**
Evidence: E5 asserts `isinstance(ms, int)` and `ms >= 0`. E4 asserts `ms: 0` for the missing toolchain. A GREEN that always writes `ms: 0` passes both.
Consequence: the event loses the build-time measurement that DL-121 asks for (plan "Checks"), and the TEST notes would record 0 ms as evidence. No wrong build result.
Resolving test: in E5 (a real run of about 0.4 s observed), assert `ms > 0`.
By: Opus (RED review, slice6b-stored-elixir)

**O3 · medium · No case shows that zero calls start no Elixir.**
Evidence: the plan ("Byte changes") says sources without a constructor field with a failure TYPE do not start Elixir; contract 3 says the compiler starts Elixir only when the call list is not empty. L2 and L3 build `slice6/decode/orders.beaml` (no `!` constructor) with `elixir` on PATH and assert no event absence. A GREEN that always starts Elixir, also with an empty call list, passes the file.
Consequence: every `--stored` build (arms, payments, slice 2 to 5) then needs `elixir` on PATH and costs about 0.4 s more, and without the toolchain it fails with the D6B-106 error where no constructor runs.
Resolving test: run L2 with `self.no_path()` and assert exit 0, empty stderr and `self.events() == []`. A store whose records match only a `!`-free signature (for example `order.jsonl` line 2 alone) with `no_path()` gives exit 0 and no event as well.
By: Opus (RED review, slice6b-stored-elixir)

## Dropped (low)

- A failure from a computed value (not a literal clause head) is not in any fixture; E4, E5 and E8 already force a real Elixir run. By: Opus (RED review, slice6b-stored-elixir)
- E1, E2 and E9a do not assert the `blocked` event result. By: Opus (RED review, slice6b-stored-elixir)

## Limits

- **[Observed]** One run on this host (macOS, Elixir 1.18.1, OTP 27). `run.py` was not run (task rule).
- **[Inference]** The pgrep probe shows the marker is visible on this host only.
- Owner decisions: none. The disposition of O1 to O3 stays pending.
