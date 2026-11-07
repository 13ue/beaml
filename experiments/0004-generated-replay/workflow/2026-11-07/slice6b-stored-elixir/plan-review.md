# Plan check: slice 6b step 13 (the `--stored` check runs the generated Elixir constructor)

**[Proposal]** PLAN CHECK, 2026-11-07. Fresh context, normal check (not Devil's Advocate). One round.
Target: [plan.md](plan.md), [plan.json](plan.json), [decisions.md](decisions.md) (D6B-102 to D6B-111) at HEAD 5bfaf5df.
Read: DL-032, DL-101, DL-102, DL-103, DL-117, DL-120, DL-121, DL-122 in [the decision log](../../../../../wiki/planning/decision-log.md); `check_stored`, `ctor_fault`, `__beaml_from_T` emit, `__beaml_valid__`, `action` in `experiments/0001-syntax-to-beam/src/main.rs`.
Probes: scratch build from `git archive HEAD` (not the repository tree). No `run.py`, no test run, no production change.
By: Opus (PLAN CHECK, slice6b-stored-elixir) for every judgement in this file.

## Verdict

**Repair required, then go.** One high objection (O1) blocks. O2 and O3 are medium and go into the same repair.
The core design holds: one batched Elixir process, static pass first, no values on disk, same block text.
By: Opus (PLAN CHECK, slice6b-stored-elixir)

## Objections

**O1 · High · The Elixir run has no time limit; a pure constructor can loop forever and the build hangs.**
- **[Observed]** Probe `rec.beaml`: `fn loop t -> String ! NoCurrency = t |> loop` (only `""` stops) and `fn Amount value, c -> Amount ! NoCurrency = c |> loop |> Amount`. The compiler accepts it (exit 0 with an empty store). DL-120 forbids EFFECTS, not recursion.
- **[Inference]** With a stored `currency: "EUR"`, the driver call never returns. Contract 3 and D6B-106 wait without a bound. The `--stored` build, the test harness and the serialized `run.py` hang. This is not a silent pass, but no error ever appears.
- **[Inference]** Second hang path: the compiler writes the full stdin JSON while the child can fill its stdout or stderr pipe (compile warnings go to stderr, observed in the plan). The plan does not say how the pipes are drained.
- Repair: add a fixed time limit (for example 30 s) around spawn and wait. On the limit, kill the child and give the D6B-106 run error with `(time limit)` in place of `(exit N)`. Write stdin, close it, then use `wait_with_output` (or drain in a thread). Event `result: "error"`. Add one guard case (E8): `rec.beaml` with a record that loops gives exit 1 and the run-error text in less than the limit plus a margin. A short limit through an env value is acceptable only for the test.
By: Opus (PLAN CHECK, slice6b-stored-elixir)

**O2 · Medium · The result protocol is loose; a wrong driver or a signal exit can give `ok` for a record that was not checked.**
- **[Verified]** Contract 5 names "non-zero exit" and "wrong count of result lines". It does not name: a signal exit (`status.code()` is `None`, an `unwrap_or(0)` reads it as success); a line that is neither `ok` nor `error <F>`; an `error F` where F is not in `self.failures[&key]`; a driver that rescues a raise and prints `ok`.
- **[Inference]** Every case gives a false pass or a wrong block text, and no planned test fails on it. E3 and E5 pin only the good path.
- Repair: state in the contract: success needs `status.success()`; exactly K lines; each line is exactly `ok` or `error <F>` with F in the failure list of that signature; any other line is the run error. The driver prints `ok` only for `{:ok, %BeamlSpike.T{}}` with T the called constructor, `error F` only for `{:error, %BeamlSpike.F{}}`, and has no `rescue`. Pin the line parser with one Rust unit test (bad line, short count, signal exit). E5 already pins `calls == 4`; keep it.
By: Opus (PLAN CHECK, slice6b-stored-elixir)

**O3 · Medium · Stored values in stderr and on disk: the DL-122 literal needs a recorded exception, a narrower print rule and no crash dump.**
- **[Verified]** DL-102 says "reports counts and reasons, never values (DL-032)". DL-122 (OWNER) says the error "names the enum, the lost literal, the count". The later and narrower OWNER decision allows the literal in stderr. The plan prints it, but records the conflict only as a limit.
- **[Verified]** Today's `kept` closure reads a record without `unknown_fields` as "kept nothing". Under D6B-108 such a record then prints any stored String as a "lost literal" (plan limit). That String can be outside data, not a former literal.
- **[Inference]** A VM crash (for example out of memory on a very large store) writes `erl_crash.dump` into the cwd with process heaps, which hold the record values. The stored file has no size limit (the 256 KiB limit applies to the source only, `lex`).
- **[Verified]** The `stored-elixir` event fields (`ts`, `source`, `action`, `target`, `result`, `ms`, `calls`) hold no source text, path or value. The stdin JSON goes only through the pipe; child output is dropped (D6B-106). These parts comply with AGENTS.md.
- Repair: record in the step 13 decision entry that DL-122 overrides DL-032 for the lost literal in stderr only (never in events or result files beyond the compiler stderr). Print the literal only when the record has the key `unknown_fields`; without the key, give the count text without the literal. Spawn the child with `ERL_CRASH_DUMP=/dev/null` (or `ERL_CRASH_DUMP_SECONDS=0`).
By: Opus (PLAN CHECK, slice6b-stored-elixir)

## Answers to the six check questions

1. **One semantics.** **[Verified]** Rust `ctor_fault` and the emitted `cond` of `__beaml_from_T` both iterate `ctor_signatures(ty)` in the same order. The one-parameter test (`Json::text` against `is_binary and String.valid?`) and the multi-key test (`get(n).text()` against `is_map and __beaml_valid__(Map.get(..))`) agree for parsed JSON. No disagreement found today. **[Inference]** A drift would be a false pass, because D6B-104 skips Elixir when the Rust pick has no `!`. Calling `__beaml_from_T` is not smaller: it is `defp` (bytes and snapshots change, against the exclusions), and it gives only `:constructor` without the failure TYPE. D6B-103 is acceptable. Note: add one guard where the first signature does not match and a later signature with `!` fails, so the mirror order is pinned. Not an objection.
2. **Constructor without `!`.** **[Observed]** No runtime reject exists. A failing pipe step in a constructor without `!` is a compile error ("pipe step Code can fail with NoCurrency, which is not in the ! list of Amount"). A failing step in a nested pipe is a compile error ("a nested pipe has the failing step Code"). Enum constructors without `!` always return a variant. D6B-104 holds. The remaining non-return is recursion (O1), not a reject.
3. **PII and events.** See O3. The event is clean. Stdin JSON reaches no log or result dir in the plan.
4. **Missing toolchain.** **[Inference]** E4 sets the env of the spawned compiler only; the developer PATH stays. Note: `PATH=/usr/bin:/bin` is not portable (a Linux host can have `/usr/bin/elixir`); an empty scratch dir as PATH is safer. A wrong Elixir version fails loud: Elixir before 1.18 has no `JSON` module (and OTP before 27 has no `:json`), so the driver raises and gives the run error. **[Unknown]** A version with the same API but other behaviour; not a likely false pass.
5. **False pass after GREEN.** See O2. An empty call list starts no Elixir and is correct only when no constructor field has a failure TYPE; E5 (`calls == 4`) pins the count for one case.
6. **Time.** **[Verified]** The plan batches all calls into one process (contract 3). **[Inference]** Bound: one VM start and compile (0.41 s observed) plus N records times M fields calls of microseconds each, plus one JSON document of the store size. Linear, no cache needed now. No streaming for very large stores (plan limit, accepted).

## What the plan repair must change

- Contract 5 and D6B-106: time limit, kill, run error; pipe draining (O1). Guard E8.
- Contract 3 and 5: strict result protocol, signal exit as error, driver without `rescue`; Rust unit test (O2).
- D6B-108 and the decision entry: DL-122 exception recorded; literal printed only with `unknown_fields`; `ERL_CRASH_DUMP` for the child (O3).
- Notes (not blocking): mirror-order guard (Q1); empty-dir PATH in E4 (Q4).

By: Opus (PLAN CHECK, slice6b-stored-elixir)
