# Slice 6b step 4: notes

## Solve

What this phase takes from the plan (step 4, D6B-14 to D6B-16, D6B-20 to D6B-24), the decision log (DL-082, DL-084, DL-085, DL-087, DL-088, DL-100) and the step 3 GREEN (G1 to G15):

- Today a variant without parentheses fails with `expected '('`. An uppercase `fn` named like an enum fails with `a constructor needs a type E` (step 3 G5).
- Today a second different signature line gives `inconsistent function signature` (step 3 G4, `ponytail:` comment).
- Today `unreachable clause: f` exists for lowercase `fn` (`main.rs`, clause coverage).
- The corpus example (`constructors.txt`) has literals and a constructor on one enum. Under DL-088 that is a compile error. The corpus is a grammar test, not a compiler fixture.
- DL-100: an enum constructor is the decode path only. Code builds variants directly. No only-way-in check.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| S1 | Undo | All RED cases go in `slice6_enum_test.py`. A Rust unit test `enum_literals_and_constructor` waits for GREEN. | Add the unit test to `main.rs` now | RED does not change the production file (task, step 3 S1). |
| S2 | Undo | Two fixtures: `slice6/enum/literals.beaml` and `slice6/enum/constructor.beaml`. | One `slice6/enum/enum.beaml` (plan) | DL-088 forbids literals and a constructor on one enum, and the task uses the name `PaymentState` for both forms. Two files keep both forms with that name. |
| S3 | Undo | The constructor fixture is `PaymentState` with `Declined(DeclineReason)` and three signatures: `status, decline_reason` (String, String), `code` (String), `n` (Int). | The plan enum `Outcome` with two signatures | The task names `PaymentState` and its runtime values. The Int signature has the same arity as the String one, so a GREEN that mixes clauses of equal arity fails (D6B-15 reason). |
| S4 | Repair | **Chose:** the clause `"declined", reason -> PaymentState = reason \|> DeclineReason \|> Declined` stays in the step 4 fixture, as the task asks. **Over:** the call form `Declined(DeclineReason(reason))`. **Because:** the task asks for "via pipe". **Commits us to:** the step 4 GREEN builds a whole-body pipe in one clause of a several-clause `fn` (the one-clause part of D6B-28) and a variant with one payload as a pipe step (D6B-26). The plan puts both in step 5. Pipes in other expression positions stay in step 5. | Call form | Task text. The plan step 5 RED keeps its own fixture. |
| S5 | Undo | `DeclineReason` is a record with a constructor without `!`: `fn DeclineReason text: String -> DeclineReason = DeclineReason { text: text }`. The runtime value is `{"PaymentState", "Declined", [%{"text" => "card"}]}`. | An enum or a failing constructor | No `with` in the pipe. A record success value stays a map (step 3 S6). |
| S6 | Undo | DL-088 text, from D6B-22: `error: enum PaymentState has literals and a constructor` and `  help: keep the literals for a 1:1 mapping or the constructor fn PaymentState, not both`. | Other text | The plan fixes it. |
| S7 | Undo | Unreachable clause: the existing text `unreachable clause: Outcome`. | A new text with `help:` | The rule is the same as for lowercase `fn`. Only the grouping per signature is new. |
| S8 | Undo | Unreachable signature, equal parameters: the step 3 text (step 3 S10). | A new text | Step 3 S10 says step 4 keeps it. |
| S9 | Undo | Unreachable signature, more parameters: `unreachable signature: Outcome` and `  help: an earlier signature line of fn Outcome has a part of these parameters and matches first; remove this one`. | The "same parameters" help line | The plan RED (b) names the superset case. "Same parameters" is wrong for a superset. |
| S10 | Undo | Literal on a payload variant: `error: enum PaymentState: the variant Declined has a payload and a literal` and `  help: a variant has a payload or a literal, not both`. A checker text, not a parser `at byte` text. | Parser error | DL-098 rule. A text that names the enum and the variant. |
| S11 | Undo | Duplicate literal: `error: enum PaymentState: the literal "ok" of Pending is unreachable, Authorized has it first` and `  help: give each variant a literal of its own`. | `duplicate literal` | D6B-23 calls it an unreachable literal. |
| S12 | Undo | The reject sources for clauses and signatures use `Approved()`. | Bare `Approved` | Then they fail today at the constructor rule, not at the parser. The bare form is covered by both fixtures. |
| S13 | Undo | D6B-23 compares `(name, TYPE)` pairs. Accept case: `code: String` then `status: String` compiles. | Reject equal TYPES with other names | D6B-23 and the D6B-16 note: the second signature has other keys, so decode can reach it. Code calls always take the first. |
| S14 | Undo | Guard: a lowercase `fn` with two different signature lines keeps `inconsistent function signature: f` (D6B-14). Passes today. | No guard | A GREEN that opens several signatures for every `fn` fails then. |
| S15 | Undo | Runtime cases call `new_PaymentState_k` directly and through code calls `from_pair`, `from_code`, `from_int` (D6B-16 static choice by arity and TYPE). | Direct calls only | The plan code list names the static call choice. |
| S16 | Undo | Build assertions: the `def new_PaymentState_k` lines, four `defp` clause lines, and source order of the first and the last clause of signature 1. The pipe clause line is not asserted. | Assert every line | The pipe clause shape depends on S4 and is checked at runtime. |
| S17 | Undo | The literal fixture asserts that no `__beaml_literal_` function is emitted. | No check | The plan: ENUM LITERALS emit no new function in this step. |

### Points the plan does not settle

- **[Unknown]** The task says "an unreachable second signature with the same parameter TYPES". This RED reads it as the same names and TYPES (D6B-23). A reject of equal TYPES with other names contradicts D6B-23 and S13. Class Repair (it changes a check). Main agent to confirm.
- **[Inference]** S4 moves two step 5 parts into step 4. The step 5 RED must then change its "today" text. Class Repair.
- **[Unknown]** A payload variant other than the keep-value variant, without a literal, in an enum with literals (`Declined(String)` beside `Unknown(String)`, D6B-21 "at most one"). Text open. No test. Class Undo.
- **[Unknown]** Text for a call `E(args)` that fits no signature (D6B-16 "names the argument TYPES"). No test. Class Undo.
- **[Unknown]** A non-exhaustive signature group of an enum constructor gives `non-exhaustive function: E` (today's text) or a text that names the signature. No test. Class Undo.
- **[Inference]** D6B-23 rejects a superset signature that a code call with more arguments can reach (plan-review.md (1), medium). The plan default stands. Class Repair (already decided in the plan).
- **[Inference]** A literal on the keep-value variant (`Unknown(String) = "x"`) is the S10 case too. No separate test. Class Undo.

## RED

Command: `python3 -B experiments/0004-generated-replay/tests/slice6_enum_test.py` (repository root). Full output: [red-output.log](red-output.log).
Result: 12 tests, 11 FAIL, 1 pass (the guard S14). Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_literal_enum_compiles` | exit 0, planned lines, no `__beaml_literal_` | `expected '(' at byte 145` | No ENUM LITERAL in the parser. |
| `test_constructor_enum_compiles_to_one_function_per_signature` | exit 0, `new_PaymentState_1..3`, clause order | `expected '(' at byte 240` | No bare variant in the parser. |
| `test_runtime_literal_enum` | 4 subtests PASS | stops at build, `expected '('` | Same. |
| `test_runtime_constructor_enum` | 12 subtests PASS | stops at build, `expected '('` | Same. |
| `test_equal_types_with_other_names_is_reachable` | exit 0 | `error: fn Outcome: a constructor needs a type Outcome` | No enum constructor. |
| `test_literals_and_constructor_on_one_enum` | S6 text | `expected '(' at byte 31` | No literal, no DL-088 check. |
| `test_unreachable_clause_after_a_catch_all` | `unreachable clause: Outcome` | `error: fn Outcome: a constructor needs a type Outcome` | No enum constructor. |
| `test_unreachable_signature_with_equal_parameters` | S8 text | `error: fn Outcome: a constructor needs a type Outcome` | Same. |
| `test_unreachable_signature_with_more_parameters` | S9 text | `error: fn Outcome: a constructor needs a type Outcome` | Same, and no subset check. |
| `test_literal_on_a_payload_variant` | S10 text | `expected '(' at byte 67` | No literal in the parser. |
| `test_duplicate_literal` | S11 text | `expected '(' at byte 31` | Same. |
| `test_lowercase_fn_keeps_one_signature_line` | `inconsistent function signature: f` | pass | Guard (S14). |

### RED checks

- Every failure is a missing behavior, not a setup failure. The compiler builds, every case reaches the compiler, every message is a compiler message.
- Each reject asserts the full message. Today's texts do not give a false pass.
- The runtime harness is the step 3 harness (`run_runtime`, no stub, `elixirc --warnings-as-errors`). Step 3 proved it against a hand-written module. Not repeated here.
- The action event check runs on every compile (no source text, no path).
- Production unchanged: `cargo test --offline --no-fail-fast` 29 pass (15 unit, 14 CLI). `slice6_int_test.py` 16 OK. `slice6_failure_test.py` 22 OK. `slice6_constructor_test.py` 25 OK.
- `run.py` was not run. No result directory was touched. No commit.

## Limits

- The pipe clause shape (S4) is checked at runtime only.
- The unreachable rejects fail today at the constructor name. They prove the rule only after GREEN accepts enum constructors.
- No test for the open points above.
