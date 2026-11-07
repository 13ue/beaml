# Slice 6b step 2: notes

## Solve

What this phase takes from the plan (step 2, D6B-04 to D6B-10, DL-092, DL-093):

- `failure_types` accepts any declared TYPE and `String`, `Int`. Today it calls `record`, so `! Int` is `unknown type: Int`.
- A new overlap check with `same_type` runs on every `fn` and every EFFECT (D6B-06, D6B-08).
- `body`/`validate`: a body can have the output TYPE or one failure TYPE. `emit` writes `{:ok, v}` or `{:error, v}` by the static TYPE.
- A record failure value is the failure struct. Struct modules are emitted for each record failure TYPE, also without an EFFECT (D6B-07).
- First RED of `plan.json`: `-> String ! String` and `-> String ! Int | String` are rejected with the D6B-09 text; `fn f x: String -> String ! Int = 5` compiles.
- Second RED: `check("")` gives `{:error, %BeamlSpike.Empty{}}`, `check("a")` gives `{:ok, "a"}`.
- Step 1 left one item: an `Int` in an EFFECT failure record (step 1 notes, GREEN Limits).

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| 1 | Undo | All RED cases go in `slice6_failure_test.py`. The Rust unit test `success_and_failure_types_never_overlap` waits for GREEN. | Add the unit test to `main.rs` now | RED must not change the production file (step 1 decision 1). |
| 2 | Undo | `overlap.beaml` holds the legal cases near an overlap (`! Int` on String, `! String` on Int, two records with other fields). `body.beaml` holds the clause and pipe cases. | One fixture | The plan names both files. |
| 3 | Undo | The `fn` overlap text is the D6B-09 text, in the `error:` / `  help:` form of the migrate messages. | The plain form without `error:` | D6B-09 gives the text with `error:` and `help:`. |
| 4 | Undo | Structural overlap: `error: fn f: the success TYPE R is also a failure TYPE: S has the same fields`, help names `S`. | The D6B-09 text with `R` only | D6B-06 asks for the same help line. Only `S` can be removed after `!`, so the help names `S`. |
| 5 | Undo | EFFECT overlap: the same error line with `effect <name>`. The help line ends after `reason: String })`. | The fn help line with "or remove ... after !" | An EFFECT needs one failure TYPE (rule kept by the plan). Removing it is no fix. |
| 6 | Undo | A body of neither TYPE: `type mismatch: expected String ! Int, got E`. A fn without `!` keeps `expected String, got E`. | Keep `expected String, got E` for all | Today's text says the failure TYPE is not allowed. That is false after D6B-05. The new text also makes the RED genuine. |
| 7 | Undo | Variant after `!`: `unknown type: Short` plus `  help: Short is a variant of the enum Why, not a TYPE; write Why`. Only the failure position is tested. | A help line in every TYPE position | D6B-10 asks for a help line that names the enum. The step is the failure position. |
| 8 | Undo | An `Int` at any depth of an EFFECT failure TYPE is rejected: `effect payments.authorize: slice 6b fails with String fields only, not O.code`. | Accept it | The failure struct gets only `reason`; an `Int` field stays `nil`. D6B-03 keeps `Int` out of the EFFECT boundary. Same pattern as the input text (step 1 G2). |
| 9 | Undo | No validity check on the `{:error, v}` value in the `def` wrapper. | Check `v` against the failure TYPES | The plan does not ask for it. The clause body is checked statically. |
| 10 | Undo | An enum failure value is the enum tuple of today (`{"Why", "Short", [v]}`); no struct module for it. | A struct for enums | D6B-04: a non-record failure has no struct module. |
| 11 | Undo | `-> String ! String \| String` keeps `duplicate name: String`. A guard test, it passes today. | The overlap text | `unique` runs first today. The guard stops a GREEN that reorders the checks. |
| 12 | Undo | The EFFECT overlap sources have one other fn and no flow fn. | A flow fn `-> O ! O` | A flow fn would overlap too and give the `fn` error first. The flow check runs later, in `validate`. |
| 13 | Undo | Runtime checks use the same harness as step 1 (`elixirc --warnings-as-errors`, `elixir -pa`), 10 cases on `body.beaml`, 4 on `overlap.beaml`. | One fixture for both | Both fixtures define `BeamlSpike`. |

### Points the plan does not settle

- **[Inference]** `emit_effect` calls `self.record(&failure).expect("checked failure")` for every TYPE in `structs()`. After GREEN, `structs()` can hold `Int` or an enum. A program with an EFFECT and a `fn ... ! Int` then panics. GREEN must filter `structs()` to records. Not tested here: an accept case with an EFFECT needs a `--stored` snapshot. Class Undo.
- **[Inference]** The orders output stays byte-identical only if struct modules keep their place when an EFFECT exists (D6B-07). The slice 5 snapshot test guards it. Class Undo.
- **[Inference]** Struct module place without an EFFECT is not fixed. The test checks the lines only, not the place. Class Undo.
- **[Unknown]** A failing fn with an `Int` failure only: is `is_integer` imported? No validity check uses it (decision 9), so no import is needed. Class Undo.
- **[Inference]** Two failure TYPES with equal fields in one list (`! A | B`): the plan does not reject them. A body `A {}` matches both by `same_type`; the struct name comes from the body TYPE name. The `{:error, _}` result is the same, so no wrong branch. Class Repair (language rule). Not tested; record for the OWNER review.
- **[Unknown]** Constructors with `!` (DL-092 `fn NonZeroInt 0 -> NonZeroInt ! IsZero`) are step 3.

## RED

Command: `python3 -B experiments/0004-generated-replay/tests/slice6_failure_test.py` (repository root). Full output: [red-output.log](red-output.log).
Result: 19 tests, 18 FAIL, 1 pass. Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_body_fixture_compiles_to_the_planned_shape` | exit 0, planned lines | `unknown type: Why` | `failure_types` accepts records only. |
| `test_overlap_fixture_compiles` | exit 0, planned lines | `unknown type: Int` | Same. |
| `test_plan_source_with_int_failure_compiles` | exit 0 | `unknown type: Int` | Same. |
| `test_runtime_body` | 10 subtests PASS | stops at build, `unknown type: Why` | Same. |
| `test_runtime_overlap` | 4 subtests PASS | stops at build, `unknown type: Int` | Same. |
| `test_same_type_both_sides` | D6B-09 text, `String` | `unknown type: String` | No overlap check; `record` rejects `String`. |
| `test_overlap_in_a_list` | D6B-09 text, `String` | `unknown type: Int` | Same. |
| `test_same_int_both_sides` | D6B-09 text, `Int` | `unknown type: Int` | Same. |
| `test_same_record_both_sides` | D6B-09 text, `R` | exit 0 | No overlap check. |
| `test_structural_records_overlap` | structural text, `R`, `S` | exit 0 | No overlap check. |
| `test_same_enum_both_sides` | D6B-09 text, `Why` | `unknown type: Why` | Records only after `!`. |
| `test_effect_overlap` | EFFECT text, `O` | `slice 1 needs exactly one pipe that calls the effect payments.authorize` | No overlap check in `effects()`. |
| `test_effect_structural_overlap` | EFFECT text, `P`, `O` | same flow text | Same. |
| `test_body_of_neither_type` | `type mismatch: expected String ! Int, got E` | `unknown type: Int` | Records only after `!`. |
| `test_body_of_neither_type_record_failure` | `... expected String ! Bad, got E` | `type mismatch: expected String, got E` | Body checked against the output only. |
| `test_pipe_ends_in_neither_type` | `... expected String ! Bad, got Int` | `type mismatch: expected String, got Int` | Same. |
| `test_variant_is_no_failure_type` | `unknown type: Short` plus help line | `unknown type: Short` | No help line. |
| `test_no_int_in_effect_failure` | `... slice 6b fails with String fields only, not O.code` | `error: stored TYPE VERSIONS unknown: ...` | No check; the `--stored` check comes next. |
| `test_duplicate_failure_keeps_its_text` | `duplicate name: String` | pass | Guard (decision 11). |

### RED checks

- Every failure is a missing behavior, not a setup failure. The compiler builds, every case reaches the compiler, every message is a compiler message.
- The runtime harness ran against hand-written modules in the planned shape (scratch, not retained, via `BEAML_SPIKE`): 14 of 14 PASS. With `piped` changed to `{:ok, 7}`, `piped_ends_in_failure` FAIL. So the runtime RED is genuine.
- Each reject asserts the full message (plan-review.md (5), step 2). Today's `unknown type: String` does not give a false pass.
- Production unchanged: `cargo test --offline --no-fail-fast` 27 pass (13 unit, 14 CLI). `slice6_int_test.py` 16 OK.

## Limits

- `elixirc --warnings-as-errors` exits 0 on unused-import warnings (Elixir 1.18.1, step 1 observation).
- No accept case with an EFFECT and a non-record `fn` failure (first point above).
- The struct module place and the `def` wrapper are not asserted.

## RED repair

Trigger: [red-review.md](red-review.md), verdict Block (objections 1 and 2 high, 3 medium).
Command: `python3 -B experiments/0004-generated-replay/tests/slice6_failure_test.py` (repository root). Full output: [red-output.log](red-output.log).
Result: 22 tests, 21 FAIL, 1 pass (the guard). Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_runtime_pipe_ends_in_record_failure` | exit 0; `pbad("q") == {:error, %BeamlSpike.Bad{reason: "q"}}` | stops at build, `type mismatch: expected String, got Bad` | The pipe body is checked against the output TYPE only (objection 1). |
| `test_effect_beside_int_failure_compiles` | exit 0, line `defp __beaml_extra(_), do: {:error, 5}`, no `defmodule Int do` | exit 1, `unknown type: Int` | `failure_types` accepts records only (objection 2). |
| `test_equal_record_failures_in_a_list` | exit 1 with the R3 text | exit 0 | `unique` compares names only (objection 3). |

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| R1 | Undo | The pipe case is a test of its own with an inline source, with a runtime check. `body.beaml` stays unchanged. | Add `mkbad` and `pbad` to `body.beaml` | In `body.beaml` the build stops at `unknown type: Why` first. The test then does not fail for the reason of objection 1. |
| R2 | Undo | The EFFECT case uses `slice2/reuse/orders.beaml` plus `fn extra x: String -> String ! Int = 5`, with `--stored stored/empty.jsonl`. It also asserts the `{:error, 5}` line. | A new fixture | The review names these files. Both exist. |
| R3 | Repair | Chose: reject `! A \| B` when A and B are plain records with equal fields. Over: allow the pair. Because: plain records are structural in this compiler; D6B-17 is nominal only for constructor TYPES. Commits us to: a later nominal-records decision relaxes this reject. Record it as DL-097 at the end of the phase. | Allow | Objection 3. `! A \| B` is then the same TYPE two times, like `! String \| String`. |
| R4 | Undo | R3 text: `error: fn f: the failure TYPE A is also a failure TYPE: B has the same fields` plus `  help: remove B after !`. | `duplicate name: B` | No compiler text exists for this case today. The text follows the structural form of D6B-06 (decision 4). `duplicate name` is false, because the names differ. |
| R5 | Undo | `compile()` in the test takes extra CLI arguments. | A second compile helper | One small change; the other tests do not change. |

### Checks

- Each new test fails for the reason that the review states. Observed above.
- Production unchanged: `cargo test --offline --no-fail-fast` 27 pass (13 unit, 14 CLI). `slice6_int_test.py` 16 OK.
- `run.py` was not run and no result directory changed (another worker runs the suite).

## GREEN

Commands and full output: [green-output.log](green-output.log). Changed file: `experiments/0001-syntax-to-beam/src/main.rs` only.

### Result (observed)

| Command | Result |
|---|---|
| `slice6_failure_test.py` | 22 tests, 18 pass, 4 FAIL (blocker below) |
| `slice6_int_test.py` | 16 OK |
| `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` | pass |
| `cargo test --offline --no-fail-fast` | 28 pass (14 unit, 14 CLI); one new unit test |
| `stored_types_test.py`, `slice3_types_test.py`, `slice4_retire_test.py` | 33, 69, 87 OK |
| `slice5_syntax_test.py`, `slice5_squash_test.py`, `slice5_rewrite_test.py` | 60, 24, 5 OK (the snapshots stay byte-equal) |

### Blocker: the runtime harness has no `ProbeSupport`

- **[Verified]** The 4 failures are the pipe subtests `piped_ends_in_failure`, `outer_passes_failure`, `outer_ok` and `test_runtime_pipe_ends_in_record_failure`.
- **[Verified]** Cause: every live pipe step is emitted inside `ProbeSupport.span(...)` (slice 1 code, not changed here). The harness compiles only `generated.ex`. So the call raises `UndefinedFunctionError: ProbeSupport.span/5`, and the check gives FAIL.
- **[Verified]** With a scratch stub `def span(_, _, _, _, f), do: f.()`, the same generated code gives `{:error, 7}`, `{:error, %BeamlSpike.Empty{}}`, `{:ok, "b"}` and `{:error, %BeamlSpike.Bad{reason: "q"}}`. These are the expected values.
- **[Inference]** The test is wrong, not the GREEN: the RED check ran on hand-written modules without spans. The GREEN did not change the test (task rule).
- Options for the main agent: (a) a RED repair adds a `ProbeSupport.span/5` stub to the harness; (b) a decision to emit no span in a pipe of a program without an EFFECT. Option (b) changes slice 1 behavior. Class of (b): Repair at least.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| G1 | Undo | `failure_types` uses `check_type`, so `String`, `Int`, records and enums pass. | A list of allowed kinds | D6B-04. `check_type` already gives `unknown type: X`. |
| G2 | Undo | The variant help line is added in `failure_types` only. | In `check_type` for every TYPE position | RED decision 7. |
| G3 | Undo | The R3 check is in `failure_types`, after `unique`. So `String \| String` keeps `duplicate name`. | A check in `overlap` | The guard test (RED decision 11). |
| G4 | Undo | One `overlap` function for `fn` and EFFECT; a flag removes the "or remove" part for an EFFECT. | Two functions | Same text; RED decision 5. |
| G5 | Undo | EFFECT order: failure TYPES, overlap, Int check (`int_inside`), then the `reason: String` rule. `! Int` on an EFFECT gives `slice 6b fails with String fields only, not Int`. | `unknown type: Int` from `record` | The task asks to reject `Int`; the new text names the cause. |
| G6 | Undo | The `reason: String` rule uses `record(..).is_ok_and(..)`. A non-record EFFECT failure now gives `effect X needs one failure type with the field reason: String`, not `unknown type`. | Keep `record(..)?` | `String` is now a known TYPE; `unknown type: String` would be false. |
| G7 | Undo | `validate` accepts a body of the output TYPE or of one failure TYPE (`same_type`). Else `type mismatch: expected O ! F1 \| F2, got T`. Without `!` the old text stays. | | RED decision 6. |
| G8 | Undo | Emit recomputes the body TYPE (`body_type`) instead of a stored map. | A `RefCell` cache from `validate` | No new state; the check runs again, cheap. |
| G9 | Undo | The struct name is the failure TYPE from the `!` list that the body TYPE matches, not the name of the body TYPE. | The body TYPE name | One failure TYPE gets one shape (D6B-07). R3 makes the match unique. |
| G10 | Undo | A record literal body gives `%__MODULE__.F{field: v}` from the literal. Another record body (variable, call, pipe end) gives `%__MODULE__.F{field: Map.get(v, "field")}`. | A runtime converter function | Smallest code. Limit: a call body is evaluated once per field (`ponytail:` comment). |
| G11 | Undo | `structs()` keeps record failure TYPES only. `emit_effect` and the new `emit_structs` use it. | Filter in `emit_effect` only | Also stops a `defmodule: 2` import for `! Int` only. |
| G12 | Undo | Without an EFFECT, struct modules come directly after the `import` line. With an EFFECT they stay in `emit_effect` (D6B-07). | After the functions | A clause body builds the struct; the module must exist first. |
| G13 | Undo | `emit_chain` takes `Option<&Clause>` instead of `fails: bool`. The REPLAY RUN passes the flow clause with owner `@parent`. | Keep `{:ok, last}` in the REPLAY RUN | A flow that ends in a failure TYPE gives the same `{:error, _}` in both runs. The payments and orders flows end in the output TYPE, so output stays byte-equal (observed). |
| G14 | Undo | New unit test `success_and_failure_types_never_overlap` (plan first RED, RED decision 1). | No unit test | The plan names it. |

### Checks

- **[Verified]** G6 import rule (step 1 review): an `Int` failure literal needs no `is_integer`, because no check validates the `{:error, v}` value (RED decision 9). `fn f x: String -> String ! Int = 5` compiles and its runtime case passes.
- **[Verified]** An EFFECT program (orders plus `fn extra "x" -> String ! Bad = Bad { reason: "x" }`) compiles in `elixirc` (exit 0), although the struct module comes after the clause. Not run.
- **[Verified]** The action event code is not changed; the failure test checks that no source text or path is in the events.
- `run.py` was not run (TEST runs it). No commit.

### Limits

- `elixirc` prints a typing warning ("clause will never match `{:ok, result}`") for a fn whose body is always a failure (`piped`). `--warnings-as-errors` does not stop on it in Elixir 1.18.1 (observed exit 0). A later Elixir can make it an error.
- The R3 reject (DL-097) is not yet in the decision log; the RED repair says "at the end of the phase".

## Harness repair

Trigger: the GREEN blocker above. Changed file: `experiments/0004-generated-replay/tests/slice6_failure_test.py` only. `main.rs` is not changed.
Commands and full output: [green-output.log](green-output.log), section "Harness repair rerun".

### Result (observed)

| Command | Result |
|---|---|
| `slice6_failure_test.py` | 22 tests, 22 OK |
| `slice6_int_test.py` | 16 OK, not changed |

### Decisions

| # | Class | Decision |
|---|---|---|
| H1 | Repair | **Chose:** the test harness supplies a `ProbeSupport` stub, `def span(_, _, _, _, f), do: f.()`, for the runtime checks (option a). **Over:** no span in pure modules (option b). **Because:** option b is D6B-28 of step 5. It changes the slice 1 output inside step 2. **Commits us to:** step 5 D6B-28 removes the need for the stub. The stub stays harmless. Decision of the main agent. |
| H2 | Undo | The stub is a constant `PROBE_SUPPORT_STUB` in the test. `run_runtime` writes it to `probe_support.ex` and compiles it with `generated.ex` in one `elixirc --warnings-as-errors` call. Alternative: define the module in `checks.exs`. Reason: the compile step then sees the module, so no undefined-module warning can come. |
| H3 | Undo | The stub does not reuse the real `ProbeSupport` of EXPERIMENT 0002 or the arm tree of slices 2 to 5. Reason: those need a Mix project and capture processes. The runtime checks need only the value of `f.()`. |
| H4 | Undo | `slice6_int_test.py` gets no stub. Reason: its 16 tests pass without it (observed). |

### Limits

- The stub does not check the span name, kind, order or function arguments. The arm tree tests of slices 2 to 5 check spans.
- `run.py` was not run. No commit.
