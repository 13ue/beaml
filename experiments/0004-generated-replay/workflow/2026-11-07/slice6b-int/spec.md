# Slice 6b step 1: the Int TYPE and integer literals

Step: [plan.md, Step 1](../slice6b-plan/plan.md#step-1-int-slice6b-int), `plan.json` step `int`.
Decisions: [D6B-02, D6B-03, D6B-47](../slice6b-plan/decisions.md).
Review note: [plan-review.md (5), Step 1](../slice6b-plan/plan-review.md). Assert the exact message text.

## Contract

- `Int` is a built-in TYPE, like `String`. A record field, a parameter and a fn output can have the TYPE `Int`.
- An integer literal (`0`, `7`) is an expression and a pattern of the TYPE `Int`.
- Clause coverage treats `Int` like `String`: literals are tags, plus an `other-int` sentinel.
- The generated module has `defp __beaml_valid__(v, <<73,110,116>>), do: is_integer(v)`.
- Literal clauses emit as Elixir integer patterns: `defp __beaml_f(0), do: ...`, `defp __beaml_f(_), do: ...`.
- A value that is not an Elixir integer fails the validity check. The fn raises `ArgumentError` "invalid BEAML input".
- `Int` is not a legal declared TYPE name. `is_integer` is not a legal fn name.

## Pass rule

- `python3 -B experiments/0004-generated-replay/tests/slice6_int_test.py`: 16 of 16 pass, 13 of 13 runtime subtests pass.
- Every reject case gives exit 1, no stdout and the exact message text in the test.
- `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` pass.
- The six compile-level test files of the plan pass. `payments.beaml` output stays byte-identical.

## Exclusions

- No arithmetic. `+` stays String concatenation (D6B-03).
- No negative literal. The lexer limit (u32) stays (D6B-03).
- No `Int` in EFFECT inputs or outputs (D6B-03). EFFECT decode stays String.
- No `Int` failure TYPE (step 2). No `Int` in enum payloads in the tests (not asked by the plan).
- Do not touch `integrations/zed-beaml/`.
