# Slice 6b step 5: a pipe in any expression position

Step: [plan.md, Step 5](../slice6b-plan/plan.md#step-5-pipe-in-any-expression-slice6b-pipe), `plan.json` step `pipe`.
Decisions: [D6B-25 to D6B-28](../slice6b-plan/decisions.md). Decision log: DL-086 in [decision-log.md](../../../../../wiki/planning/decision-log.md).
Step 4 base: [slice6b-enum/red-review.md](../slice6b-enum/red-review.md) ("Step 5 after S4"), [slice6b-enum/notes.md](../slice6b-enum/notes.md) (S4, R1, R2).
Step 3 base: [slice6b-type-constructor/review.md](../slice6b-type-constructor/review.md) (G13, spans per pipe).

## Contract

- A pipe `|>` may stand in any expression position: a call argument, a record field value, a clause body (DL-086).
- `|>` binds weaker than `+`. `a + b |> f` is `f(a + b)`. A pipe ends at `,`, `)` and `}` (D6B-25, notes.md S5).
- A step is a bare name: a 1-input `fn`, an EFFECT, a constructor with one input, or a variant with exactly one payload (D6B-26).
- A variant step with zero or two payloads gives `pipe step V must take one argument`. A wrong input TYPE gives `type mismatch in pipe step V: expected T, got U` (notes.md S8).
- A lowercase step that is not a `fn` (for example a variable) gives `unknown pipe step: x`, also in a nested pipe.
- A nested pipe (not the whole body) with an EFFECT step or a failing step is a compile error (D6B-27). Text: `error: fn F: a nested pipe has the EFFECT step S` or `error: fn F: a nested pipe has the failing step S`, then `  help: make the pipe the whole body` (notes.md S6).
- A whole-body pipe without an EFFECT step may stand in a several-clause `fn`. A failing step in it compiles to a `with`; a failure stops the pipe and gives `{:error, e}`. No spans (D6B-28).
- The `!` rule stays: a failing step needs its failure TYPE in the `!` list of the enclosing `fn`. Existing text.
- A whole-body pipe with an EFFECT step keeps the one-clause rule, `emit_chain` and spans (D6B-28, step 4 R1).
- A nested pipe compiles to plain nested calls (`build(prepare(p), x)`).
- A pipe that reaches an EFFECT only through another `fn` has no span. This is today's behavior. A change is an OWNER question on D6B-28 (step 3 review, G13). Not changed here.

## Pass rule

- `python3 -B experiments/0004-generated-replay/tests/slice6_pipe_test.py` (repository root): 11 of 11 pass, all runtime subtests pass, no ProbeSupport stub.
- Every reject gives exit 1, no stdout and the exact text in the test.
- The guards stay green: `bad/*.beaml` texts (S13); the orders outputs and `payments.beaml` stay byte-equal (S12).
- `cargo test --offline --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` pass.
- `slice6_int_test.py`, `slice6_failure_test.py`, `slice6_constructor_test.py`, `slice6_enum_test.py` and the slice 3 to 5 compile-level tests pass.

## Exclusions

- Steps with arguments (`|> f(x)`, D6B-25).
- Nested failing steps lifted into a `with` (D6B-27 forbids them in 6b).
- Spans for pure pipes or for a pipe that reaches an EFFECT through a `fn` (OWNER question on D6B-28).
- `redacted` and `with` (step 6). Decode (steps 7, 8).
- Do not touch `integrations/zed-beaml/`.
