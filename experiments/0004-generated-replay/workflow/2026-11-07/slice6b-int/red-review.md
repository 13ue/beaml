# Slice 6b step 1: RED review

Reviewer: a fresh-context agent. Type: RED REVIEW, not a Devil's Advocate.
Inputs: spec.md, notes.md, red-output.log, `../slice6b-plan/` (plan.md step 1, decisions.md D6B-02, D6B-03, D6B-47, plan-review.md (5)), `tests/slice6_int_test.py`, `slice6/int/int.beaml`, `experiments/0001-syntax-to-beam/src/main.rs`.

## Verdict

**PASS. GREEN can start.** No critical or high objection. One medium note.

## Rerun (observed)

- Command: `python3 -B experiments/0004-generated-replay/tests/slice6_int_test.py` (repository root).
- Result: 16 tests, 15 FAIL, 1 pass (`test_no_negative_literal`, a guard). Equal to red-output.log.
- Working tree clean after the run. No production file changed.

## Checks

**Failures are genuine (observed)**
- The compiler builds and runs. Every failure text is a compiler message: `expected expression or pattern at byte N` (no Number in `node()`), `unknown type: Int` (`check_type`), or exit 0 (reserved names).
- `test_runtime` fails at `assert_built`. That is the same missing parse, not a setup fault.

**Messages against the plan and the decision log (observed)**
- Plan step 1 first RED sources: compile, `non-exhaustive function: f`, type mismatch. The test asserts the exact text (plan-review.md (5)).
- `type mismatch: expected {expected}, got {actual}` is the `require_type` text in main.rs.
- `1 + 2`: `expression` checks each `+` side against `String`. So `expected String, got Int` is today's rule, not a new one.
- EFFECT output text is the slice 1 text in main.rs. It stays unchanged.
- DL-092 needs `Int` patterns and `n: Int` parameters. The fixture has both forms (`fn f 0`, `fn f n: Int`). DL-093 `! Int` is step 2.

**False-pass search (observed)**
- Reject cases compare the tuple (exit, stdout, full stderr). A wrong exit 0 or a near text fails.
- Runtime: every one of the 13 names must print PASS. A missing line gives `None` and fails. A crash or a missing `:json` (OTP 27 present) fails all subtests.
- `is_integer` guard: the fixture test asserts the exact `__beaml_valid__` line. `elixirc` fails if `is_integer` is not imported (`import Kernel, only:`). `f(0.0)` and the JSON float `7.0` catch an `is_number` guard.
- An `is_integer` import in every module changes `payments.beaml` output. slice5_syntax_test, drift_test and cli.rs catch it.
- `seven() == 7` catches a literal emitted as a binary. The two short accept cases only check exit 0, but the fixture covers their emit.

**EFFECT exclusion (D6B-03) (observed)**
- Consistent. The plan excludes `Int` in EFFECT inputs and outputs. Decision 2 tests JSON decode through the fn validity check only.

**Worker Undo choices**
- Decisions 5, 6, 8, 9 (reject texts, reserved `Int` and `is_integer`): Undo is correct. They change no stored record and no OWNER-visible result. A later text change is a revert.
- `is_integer` import only when `Int` is used: Undo. It is an emit detail. The byte-identical snapshot tests keep it honest.
- Decision 1 (Rust unit test `int_literals_and_patterns` waits for GREEN): the Python RED has the same three sources with exact text. Low; dropped.

## Objections

### N1 · medium · The EFFECT input guard checks one shape only

- **Wrong outcome.** main.rs checks the EFFECT input with `check_type` only, so a nested record or a direct TYPE is legal there. A GREEN that checks only top-level fields of the input record passes `test_no_int_in_effect_input`. Then `type I { inner: J }` with `type J { n: Int }`, or `effect ... Int -> P`, sends a JSON number. That number goes into the `request` of the stored RESPONSE RECORD. D6B-03 is then broken without a failing test.
- **Smallest test.** Two reject cases: a nested input record with an `Int` field, and `Int` as the direct EFFECT input TYPE. Each expects exit 1 and an EFFECT input reject.
- **Disposition.** Pending. Not blocking: the test can come in GREEN or in TEST. The message text for the direct case is a new Undo choice.

## Limits

- `cargo test`, fmt and clippy were not rerun. notes.md reports 25 pass.
- The hand-written runtime module of the worker is not retained. Its 13 of 13 PASS is not checked here.
- Literals above the u32 lexer limit are not tested. D6B-03 excludes them.
