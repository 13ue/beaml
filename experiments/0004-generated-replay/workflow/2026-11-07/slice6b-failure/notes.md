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
