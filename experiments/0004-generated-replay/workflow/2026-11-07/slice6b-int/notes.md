# Slice 6b step 1: notes

## Solve

What this phase takes from the plan (step 1, D6B-02, D6B-03, D6B-47):

- `node()` accepts `Token::Number` as an Int node. `check_type` knows `Int`. `pattern`, `expression`, `normalized`, `useful` and `emit_node` handle it.
- Coverage uses an `other-int` sentinel, like `other-string`. Validity is `is_integer(v)`.
- First RED cases of `plan.json`: source 1 compiles; source 2 is `non-exhaustive function: f`; source 3 is a type mismatch.
- Runtime: `f(0)` and `f(7)` give the two texts; `f("0")` raises `ArgumentError`.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| 1 | Undo | All RED cases go in `slice6_int_test.py`. The Rust unit test `int_literals_and_patterns` waits for GREEN. | Add the unit test to `main.rs` now | RED must not change the production file. The cargo count must stay 25. |
| 2 | Undo | "Decode of an integer from JSON" is tested as `unbox(:json.decode(...))` through the fn validity check. | Decode in an EFFECT output | D6B-03 excludes `Int` in EFFECT outputs. The fn wrapper is the only decode path left. |
| 3 | Undo | The typed reason of a non-integer value is the existing `ArgumentError` "invalid BEAML input". | A new reason text | The fn wrapper has this reason today. The plan names `ArgumentError`. |
| 4 | Undo | Runtime rejects also cover `7.0` and `null`. | Only `"0"` and `"7"` | A float is the likely false pass for "a number". |
| 5 | Undo | Reject: `type Int { ... }` gives `invalid type name: Int`. | Allow a user TYPE `Int` | `String` has the same rule. A user `Int` would shadow the built-in TYPE. |
| 6 | Undo | Reject: an `Int` field in an EFFECT input gives `effect payments.authorize: slice 6b sends String fields only, not I.n`. | No check; Int input fields become legal JSON numbers | D6B-03 says no `Int` in EFFECT inputs. Without a check GREEN makes them legal silently. The text follows the slice 1 output rule. |
| 7 | Undo | Reject: an `Int` field in an EFFECT output keeps the slice 1 text `slice 1 decodes String fields only, not P.n`. | A new text | Every existing reject keeps its message (plan, common rules). |
| 8 | Undo | Reject: `fn is_integer` gives `invalid function name: is_integer`. | No reservation | The plan shape calls `is_integer(v)`, so the module imports it, like `is_binary`. |
| 9 | Undo | `1 + 2` with output `Int` gives `type mismatch: expected String, got Int`. | A new "no arithmetic" text | `expression` checks each `+` side against `String` today. The smallest GREEN keeps that rule. |
| 10 | Undo | Fixture only, no random-name template run. | A Fixture and a Template class, as in slice 3 and 5 | Names do not change the Int logic. Random literals add no new path. |
| 11 | Undo | `-1` keeps today's `unsupported token at byte 14`. This case passes today; it is a guard. | Leave it out | D6B-03 says no negative literal. The guard stops a GREEN that adds one. |

### Points the plan does not settle

- **[Inference]** The plan shape `do: is_integer(v)` needs `is_integer: 1` in `import Kernel, only: [...]`. The `payments.beaml` output must stay byte-identical. So GREEN must add the import and the Int validity clause only when the program uses `Int`, or the snapshot changes. Class Undo (emit detail, reversible).
- **[Inference]** Decision 6 (EFFECT input text) is a new message. Class Undo. GREEN may change the text if the OWNER or the caller prefers no check.

## RED

Command: `python3 -B experiments/0004-generated-replay/tests/slice6_int_test.py` (repository root). Full output: [red-output.log](red-output.log).
Result: 16 tests, 15 FAIL, 1 pass. Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_fixture_compiles_to_the_planned_shape` | exit 0, planned Elixir lines | exit 1, `expected expression or pattern at byte 127` | `node()` does not accept a number. |
| `test_literal_clause_and_int_parameter_compile` | exit 0 | exit 1, `expected expression or pattern at byte 5` | Same. |
| `test_int_output_and_literal_expression_compile` | exit 0 | exit 1, `expected expression or pattern at byte 18` | Number token. |
| `test_runtime` | 13 subtests PASS | stops at build, exit 1 | Same. |
| `test_literal_alone_is_non_exhaustive` | `non-exhaustive function: f` | `expected expression or pattern at byte 5` | Same. |
| `test_string_body_for_int_output` | `type mismatch: expected Int, got String` | `unknown type: Int` | `check_type` knows `String` only. |
| `test_int_body_for_string_output` | `type mismatch: expected String, got Int` | `expected expression or pattern at byte 17` | Number token. |
| `test_int_literal_against_string_parameter` | `type mismatch: expected String, got Int` | `expected expression or pattern at byte 34` | Number token. |
| `test_literal_after_catch_all_is_unreachable` | `unreachable clause: f` | `expected expression or pattern at byte 33` | Number token. |
| `test_equal_literals_are_unreachable` | `unreachable clause: f` | `expected expression or pattern at byte 5` | Number token. |
| `test_no_plus_on_int` | `type mismatch: expected String, got Int` | `expected expression or pattern at byte 14` | Number token. |
| `test_int_is_not_a_declared_type_name` | `invalid type name: Int` | exit 0 | Only `String` is a reserved TYPE name. |
| `test_is_integer_is_a_reserved_function_name` | `invalid function name: is_integer` | exit 0 | Not in the reserved list. |
| `test_no_int_in_effect_output` | `... slice 1 decodes String fields only, not P.n` | `unknown type: Int` | `check_type` runs first. |
| `test_no_int_in_effect_input` | `... slice 6b sends String fields only, not I.n` | `unknown type: Int` | Same. |
| `test_no_negative_literal` | `unsupported token at byte 14` | pass | Guard (decision 11). |

### RED checks

- Every failure is a missing behavior, not a setup failure. The compiler builds, every case reaches the compiler, every message is a compiler message.
- The runtime harness ran against a hand-written module in the planned shape (scratch, not retained): 13 of 13 PASS. So the runtime RED is genuine.
- The reject cases assert the full message, so today's errors do not give a false pass (plan-review.md (5)).
- Production unchanged: `cargo test --no-fail-fast` 25 pass (11 unit, 14 CLI). `slice5_syntax_test.py` 60 OK.

## Limits

- `elixirc --warnings-as-errors` exits 0 on unused-import warnings (Elixir 1.18.1, observed). An unused `is_integer` import does not fail the runtime test.
- The Template run (random names) is not used (decision 10).
