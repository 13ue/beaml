# PROBE C3: cause of the DRIFT crash run

Target: `results/20261107T171545190446Z/` (crash run) against `results/20261107T180431928222Z/` (TEST of steps 12 and 13). Read-only probe. No `run.py` run, no compiler build. By: Opus (PROBE C3) on every judgement.

## 1. Which state produced the crash run

- **[Observed]** `run.py` line 133 names run directories in UTC. `171545Z` is 18:15:45 +0100 local. The `17:00` to `17:30` git window in the task is local time and does not contain this run.
- **[Observed]** Local commits around it: `a42a701c` 18:11:00 (steps 12/12b RED review PASS), then `237a4578` 18:45:00 (steps 12/12b GREEN). No compiler or `probe_support.ex` commit falls between them.
- **[Observed]** `commands.json` records no compiler hash. The generated code is retained: `R/gen/orders.generated.ex`, `R/gen/payments.generated.ex` and `gen/baseline/orders.generated.ex` are byte-equal (sha256) in both runs. The orders module has the D6B-114 clause `_ = ProbeSupport.event(...)` at line 36.
- **[Observed]** `main.rs` at `45f43bc2` (last compiler commit before `237a4578`) has 0 `_ = ProbeSupport.event` emitters; at `237a4578` it has 1.
- **[Inference]** The crash run used the uncommitted working tree of the GREEN 12 worker: step 12 compiler present, D6B-127 not yet in `probe_support.ex`. The retained `drift.json` was committed later with `237a4578`.

## 2. The FunctionClauseError

- **[Observed]** `eval-flow.stdout` for R, N and Q: `result` has the single key `raised` with the value `FunctionClauseError`; `host_validation` is `nil`; `transport` is 0 (no Payments exchange). `eval-flow.stderr` is empty (0 bytes). `eval-repaired-flow.stdout` has the same shape.
- **[Unknown]** Function and arity from the run evidence. The probe keeps only `inspect(error.__struct__)`; no stacktrace is retained.
- **[Inference]** It is `:otel_span.hex_trace_id/1` with the argument `:undefined` (no span context), called from `ProbeSupport.event/2`. Source: GREEN 12 notes, "Fail, cause A" (`notes.md` lines 112 to 114): same exception, same call path (`place` with no open span), observed there in 19 tests.

## 3. D6B-114/127 window or other cause

- **[Inference]** The D6B-114/127 window. Evidence: generated code equal in both runs, so the difference is host side; `transport` 0, so the crash is before the EFFECT call, where the moved `prepared` event stands; `probe_support.ex` at `a42a701c` has 0 `"none"` literals, at `237a4578` it has 2 (D6B-127).
- **[Observed]** No other host change shows in the evidence. **[Unknown]** The exact `probe_support.ex` bytes of the crash tree (the scratch tree is deleted).

## 4. Did committed `main` ever produce this crash

- **[Observed]** 59 retained `drift.json`. Only `171545Z` has `untyped_crash` on the GEN arm. Every later run has R `false_reject`, N `false_reject`, Q `typed_reject`: `173218Z` (18:32 local, after D6B-127, before its commit), `175013Z`, `180431Z`, `181807Z`. Earlier `untyped_crash` rows are LIB arm only (LIB left DRIFT in step 6a).
- **[Inference]** No committed state of `main` produced it. `237a4578` brings the D6B-114 emitter and the D6B-127 fix together; no commit has one without the other. **[Unknown]** No retained run at exactly `1dd6ad62` (last run 19:18 local, HEAD 19:46).

## 5. Smallest rule so this run fails

- Location: `experiments/0004-generated-replay/run.py` line 609 (`summary["status"] = ...`). **[Observed]** `repaired_all` is `true` in the crash run (all repaired evals exit 0), so `repaired_all` alone does not catch it.
- **[Proposal]** Pin of the expected classes (strongest, one line; also catches a drift to `wrong_accept`):

```python
summary["status"] = "pass" if summary["freeze"]["status"] == "pass" and repaired and {d: summary["drift"][d]["gen"]["new_live"] for d in DERIVATIVES} == {"R": "false_reject", "N": "false_reject", "Q": "typed_reject"} else "fail"
```

- Weaker one-line option: `... and repaired and all(summary["drift"][d][a]["new_live"] != "untyped_crash" for d in DERIVATIVES for a in ARMS)`. It catches this run, but not a change between the reject and accept classes.
- **[Proposal]** The pin changes when a DRIFT derivative changes on purpose. That is the wanted trigger.
