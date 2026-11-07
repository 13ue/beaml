# Plan: slice 6b step 13, the `--stored` check runs the generated Elixir constructor over the stored values

**[Proposal]** PLAN phase, 2026-11-07. Task records only. No production file, no test file, no commit, no `run.py` run.
Decisions: DL-121 (Q6B-19, b; closes D017 and P11) and DL-122 (Q6B-8, A; closes D007) in [the decision log](../../../../../wiki/planning/decision-log.md). Also read: DL-101, DL-102, DL-103, DL-105, DL-106, DL-116, DL-117, DL-120; D019 in [decisions to be made](../../../../../wiki/planning/decisions-to-be-made.md); [step 8 review](../slice6b-decode-constructor/review.md) (D1, probe 6) and [notes](../slice6b-decode-constructor/notes.md) (G7, P11); the [step 6a spec](../slice6b-records-v2/spec.md) (`value`, `version 2`, `value_sha256`); `experiments/0001-syntax-to-beam/src/main.rs` at HEAD 2f211da7 (`check_stored`, `ctor_fault`, `__beaml_from_T`, `build_with_refusals`, `action`).
Design decisions that DL-121 and DL-122 do not settle: [decisions.md](decisions.md) (D6B-102 to D6B-111). No OWNER question. Machine form: [plan.json](plan.json).
By: Opus (PLAN, slice6b-stored-elixir) for every proposal in this file (DL-107).

## Facts the step builds on (observed at HEAD 2f211da7, scratch build from `git archive`)

- **[Verified]** `check_stored` reads each record line. It checks the record version 2 (D6B-59), the TYPE VERSION path, the literal enum fields (DL-102 "no variant", DL-103 note) and the constructor fields. All DL-102 lines are given only when no path error exists.
- **[Verified]** `ctor_fault` picks the first signature whose keys all hold Strings (one parameter: the field value is the String; D6B-48). Then the static body TYPE of the first matching clause decides (G7). The `ponytail:` comment names the false pass.
- **[Verified]** The generated `__beaml_from_T` uses the same signature rule in a `cond`. It calls the public `new_T_k(...)`. Only a constructor with a failure TYPE can give `:constructor`; a constructor without `!` returns its value.
- **[Verified]** `new_T_k` returns `{:ok, %BeamlSpike.T{...}}` or `{:error, %BeamlSpike.F{...}}` after step 11.
- **[Observed]** Probe 6 reproduces. `pipe.beaml` below with the record `amount: {"value":"","currency":"EUR"}`: `--stored` exit 0, empty stderr. The nested form (`c |> Code |> unwrap |> Amount`, `Code` fails on `""`) also gives exit 0.
- **[Observed]** The same `--stored` run with `PATH=/usr/bin:/bin` gives exit 0 today. No Elixir runs.
- **[Observed]** DL-122 case: `slice6/decode/orders.beaml` without `Pending = "pending"` (or with `Pending = "wait"`) and `slice6/decode/stored.jsonl` give exit 0, empty stderr. Line 2 holds `"pending"` with `unknown_fields: []`, so it was a literal at capture time.
- **[Observed]** Mechanism probe: one `elixir -e <driver>` process reads `{"module": <generated source>, "calls": [[fun, args], ...]}` as JSON on stdin, runs `Code.compile_string/1` and `apply(BeamlSpike, fun, args)`. Results: `["","EUR"]` gives `{:error, NoCurrency}` (pipe), `["1",""]` gives `NoCurrency` (nested), `["1","EUR"]` gives ok. Wall time 0.41 s (Elixir 1.18.1, OTP 27). Compile warnings (undefined `ProbeSupport`, `:otel_*`) go to stderr only; the compile does not fail.
- **[Observed]** The compiler rejects a non-exhaustive constructor (`non-exhaustive function: Amount`). With DL-120 a constructor is pure. A raise in the Elixir run is therefore a compiler defect, not a data case.

## Contract

1. **Static first pass, unchanged order** (DL-121). Record version, TYPE VERSION path, orphans, literal rules ("no variant", DL-103 note), the new DL-122 lost-literal rule, "no signature". Any static error ends the check with today's text. Elixir does not start (D6B-105).
2. **DL-122 lost literal, static** (D6B-108). A stored String of a literal enum field that is not in the record's `unknown_fields` and is no current ENUM LITERAL blocks. One message per (TYPE, operation, field, enum, literal):

   ```
   error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize has the ENUM LITERAL "pending" of PaymentState for field state, and PaymentState has no such literal now
     record source: S:2 (line 2)
     help: declare the fate in a MIGRATE STEP (DL-122); slice 6b has no MIGRATE STEP form for an enum field (D6B-39), so restore the literal "pending" in PaymentState
   ```

   Plural: `RECORDS`, `have`. The literal is written with `json_string` (one line, escaped).
3. **Elixir pass** (DL-121, D6B-102 to D6B-104). Only when the static pass is clean. For each record and each constructor field whose first matching signature has a failure TYPE, the check adds one call `[new_T_k, [inputs]]`. When the list is not empty, the compiler starts one `elixir -e <DRIVER>` with the module of `checker.emit(service)` and the calls as JSON on stdin. The driver prints one line per call, in order: `ok` or `error <FailureType>`. The static clause-body decision of `ctor_fault` is removed.
4. **Same text as today.** An `error F` line goes into the existing `faults` map as `Some(F)`. The DL-102 block text, the count, the first `record source: S:N (line N)` line and the help line stay byte-equal to the step 8 form.
5. **No pass without Elixir** (D6B-106). `elixir` not found gives:

   ```
   error: the --stored check runs the constructors over the stored values in Elixir (DL-121): elixir is not on PATH
     help: install Elixir 1.18 with Erlang/OTP 27 and put elixir on PATH
   ```

   A non-zero exit or a wrong count of result lines gives `error: the --stored check: the Elixir run of the generated constructors failed (exit N)` plus `help: compile the generated module with elixirc to see the error`. Exit 1 in both cases.
6. **No values out** (DL-032, DL-105). The record values go only through the stdin pipe of the child. No file holds them. The driver prints only `ok` and failure TYPE names. The compiler never forwards Elixir stdout or stderr (a raise prints its arguments).
7. **Event** (D6B-107). Each Elixir run appends `{"action":"stored-elixir","result":"ok"|"blocked"|"error","ms":N,"calls":K}` through `action()`. No source text, no path, no value. A missing `elixir` gives `result: "error"`, `ms: 0`.
8. **Order inside `build_with_refusals`.** `checker.emit(service)` moves before `check_stored`; the same code string goes to the check and to `Build.code`. `--remove-dead` rechecks call `build`, so they run the same check.

## First failing test: `tests/slice6_stored_elixir_test.py`

Harness: `sf.Slice6Failure.setUp`, `compile` (it also checks that events hold no source path and no source text) and `sd.Slice6Decode.assert_rejected` (exact stderr, exit 1, no stdout). Fixtures in `slice6/stored-elixir/` (D6B-110):

- `pipe.beaml`: `slice6/decode-ctor/orders.beaml` with the Amount block replaced by review probe 6:
  `fn cur v: String -> String ! NoCurrency`, `fn cur "" -> String ! NoCurrency = NoCurrency {}`, `fn cur v -> String ! NoCurrency = v`, `fn Amount value: String, currency: String -> Amount ! NoCurrency`, `fn Amount value, c -> Amount ! NoCurrency = value |> cur |> Amount`, `fn Amount value: String -> Amount`, `fn Amount value -> Amount = Amount { value: value, currency: "EUR" }`.
- `nested.beaml`: the same with `type Code { text: String }`, `fn Code text: String -> Code ! NoCurrency` (`""` fails, other gives `Code { text: t }`), `fn unwrap Code { text } -> String = text`, `fn Amount value, c -> Amount ! NoCurrency = c |> Code |> unwrap |> Amount`, second signature `fn Amount currency: String -> Amount`.
- `pipe-fail.jsonl`: line 1 of `decode-ctor/stored.jsonl` with `amount: {"value":"","currency":"EUR"}`; `nested-fail.jsonl`: with `amount: {"value":"1","currency":""}`. Each with a new `trace_id` and `value_sha256` from `stored_types_test.value_sha256`. The Payment fields do not change, so the `type` key stays.

Cases:

- **E1 (first RED, probe 6).** `pipe.beaml --stored pipe-fail.jsonl`: exit 1, no stdout, stderr exactly
  `error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize fails the constructor of Amount for field amount with NoCurrency` + `  record source: <path>:1 (line 1)` + the step 8 `HELP_MIGRATE` line. Today: exit 0, empty stderr (observed).
- **E2 (RED, nested constructor).** `nested.beaml --stored nested-fail.jsonl`: the same text. Today: exit 0 (observed).
- **E3 (guard, passes before and after).** `pipe.beaml --stored decode-ctor/stored.jsonl`: exit 0, empty stderr, and the event `stored-elixir` with `result: "ok"` exists after GREEN (that part is RED today: no event). Fails on a GREEN that blocks every record or prints Elixir warnings.
- **E4 (RED, missing toolchain).** E1 with `env PATH=/usr/bin:/bin`: exit 1, stderr exactly the D6B-106 text. Today: exit 0 (observed). Fails on a GREEN that skips the check when `elixir` is missing.
- **E5 (RED, timing event).** After E3: the last `stored-elixir` event has an Int `ms >= 0`, `calls == 4` (four records of `stored.jsonl`, one Amount call each), and no key other than `ts`, `source`, `action`, `target`, `result`, `ms`, `calls`. The harness checks no source text and no path.
- **E6 (guard, no Elixir for a static error).** `pipe.beaml --stored decode-ctor/stored-nomatch.jsonl` with `PATH=/usr/bin:/bin`: exit 1 with today's exact "matches no signature" text, not the toolchain text. Passes today; fails on a GREEN that starts Elixir before the static pass ends.
- **E7 (guard, no value in output).** E1 and E2 stderr and the events do not contain `EUR` or the record `trace_id`.
- **L1 (RED, DL-122 removed literal).** `slice6/decode/orders.beaml` text without `Pending = "pending"  ` (inline, as `test_written_record_reports_the_count` does) `--stored slice6/decode/stored.jsonl`: exit 1, stderr exactly the D6B-108 text with count 1, line 2. Today: exit 0 (observed).
- **L1b (RED, DL-122 changed String).** The same with `Pending = "wait"`: the same text. Today: exit 0 (observed).
- **L2 (guard, passes before and after).** The unchanged `orders.beaml` with `stored.jsonl`: exit 0, empty stderr. Line 3 (`"refunded"`, kept in `unknown_fields`) does not block. Fails on a GREEN that blocks every non-literal String.
- **L3 (guard, passes before and after).** The unchanged source with `stored-resolved.jsonl`: the DL-103 note stays, no block.

## Existing assertions that change (each by name)

| File | Assertion | Today | After step 13 |
|---|---|---|---|
| `slice6_decode_test.py` | `test_written_record_reports_the_count`, its `run_runtime` call | builds the source without `Pending` with `--stored stored.jsonl` (default `stored=STORED`) | passes `stored=sf.EMPTY_STORED`: line 2 `"pending"` now blocks under DL-122; the test needs no stored records for its runtime build |

- Not changed, but now produced by the Elixir pass: `slice6_decode_ctor_test.py` `test_stored_record_fails_the_record_constructor` (same text, count 2, line 2) and `test_stored_records_pass_the_constructors` (stderr stays empty). The GREEN worker runs both.
- Not changed: `test_stored_record_matches_no_signature` (static), every `slice6_decode_test.py` reject text, every test that uses `stored/empty.jsonl`.
- **[Inference]** No other test builds a literal enum source against records with a lost literal (grep of `--stored` users; arms, slice 2 to 5 and payments have no enum).

## Byte changes

- **None in generated Elixir.** `emit` does not change. Every stdout pin (S12 of `slice6_pipe_test.py`, H8 of `slice6_host_struct_test.py`, `payments.generated.snapshot`) stays.
- **Change:** stderr and exit code of `--stored` runs that hit P11 or DL-122; one new event line per Elixir run.
- **No Elixir start** for sources without a constructor field with a failure TYPE: every arm, slice 2 to 5, payments, `slice6/decode`, the enum-constructor-only outputs. Their build time does not change.

## Checks

- `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` (0001).
- The new test file; `slice6_decode_test.py`, `slice6_decode_ctor_test.py`, `slice6_host_struct_test.py`, every other `slice6_*_test.py`, the six compile-level test files.
- `python3 -B experiments/0004-generated-replay/run.py` once at the TEST phase, serialized with other workers.
- Record the `stored-elixir` `ms` of E3 and of the decode-ctor runs in `notes.md` (DL-121 asks the step to measure build time).

## Test-first rule

Applies. E1, E2, E4, E5, L1 and L1b are behaviour RED. E3, E6, E7, L2 and L3 are guards; the RED review does not count them as RED.

## Exclusions

- No Rust NIF, no second backend (D019 stays open). No compiler evaluator (DL-121 rejects option a).
- No change of the runtime decode, of `__beaml_from_T`, of `T.new/1` or of any generated byte.
- Lost mappings of constructor enums (an old value that a changed enum constructor now maps to the keep-value variant) are not checked (D6B-109).
- A literal that moves from one known variant to another (DL-103 limit). No count for it.
- No MIGRATE STEP form for an enum field (D6B-39, DL-122 interim). No `quarantine` syntax.
- Records of other environments: one `--stored` file is one environment (as today).
- `integrations/zed-beaml/`.

## Limits

- **[Inference]** The signature choice stays in Rust and mirrors the `cond` of `__beaml_from_T` (D6B-103). A new signature rule must change both. The `ponytail:` comment names it.
- **[Inference]** One `elixir` start costs about 0.4 s per build with such a constructor field. No cache.
- **[Inference]** `elixir` from asdf resolves its version from `~/.tool-versions` when the compiler runs in a temporary cwd. A machine with only a project-local `.tool-versions` gets the D6B-106 run error, not a pass.
- **[Inference]** A record without the key `unknown_fields` counts as "kept nothing" (today's `kept` closure). A non-literal String in it then blocks under DL-122. Version 2 records of literal outputs always have the key.
- **[Inference]** DL-122 asks for the lost literal in the text. It is a value of the record. It is printed because the record says it was an ENUM LITERAL at capture time (not in `unknown_fields`). A hand-edited record can put other text there.
- **[Unknown]** Very large RECORD SNAPSHOTS: one JSON document on stdin, no streaming. Not measured.
