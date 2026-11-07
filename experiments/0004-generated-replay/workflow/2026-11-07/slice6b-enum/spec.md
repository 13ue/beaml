# Slice 6b step 4: ENUM LITERALS or an enum constructor

Step: [plan.md, Step 4](../slice6b-plan/plan.md#step-4-enum-literals-and-enum-constructor-slice6b-enum), `plan.json` step `enum`.
Decisions: [D6B-14 to D6B-16, D6B-20 to D6B-24](../slice6b-plan/decisions.md). Decision log: DL-082, DL-084, DL-085, DL-087, DL-088, DL-100 in [decision-log.md](../../../../../wiki/planning/decision-log.md).
Step 3 base: [slice6b-type-constructor/notes.md](../slice6b-type-constructor/notes.md) (signature lines, `fn_name`, `same_type`, `elixir_name`, spans per pipe).

## Contract

- A variant without parentheses is legal in an `enum`, in patterns and in expressions. `A` means `A()` (D6B-20). `A()` stays legal.
- A variant may have a literal: `Authorized = "ok"`. A variant has a payload or a literal, not both (DL-098).
- In an enum with literals, each literal is unique. A second equal literal is unreachable (D6B-23).
- An uppercase `fn E` with `E` an enum is an enum constructor. It returns `E`.
- An enum has literals or a constructor, not both (DL-088, text D6B-22).
- An enum constructor may have several signature lines. Each clause belongs to the nearest earlier signature line (D6B-13). A lowercase `fn` keeps one signature line (D6B-14).
- A signature line is unreachable when every `(name, TYPE)` of an earlier one is also in it (D6B-23). A clause that an earlier clause of the same signature always matches is unreachable (DL-087).
- Each signature compiles to `def new_E_k` (k from 1 in source order) with its private clauses `__beaml_new_E_k` in source order (D6B-15, D6B-24).
- A call `E(args)` takes the first signature whose arity and TYPES fit (D6B-16).
- Code builds variants directly in any `fn` (DL-100). No only-way-in check for enums.
- ENUM LITERALS emit no new function in this step. Decode is step 7 and step 8.
- Exact texts: [notes.md](notes.md), decisions S6 to S11.

## Pass rule

- `python3 -B experiments/0004-generated-replay/tests/slice6_enum_test.py` (repository root): 19 of 19 pass (the guards S14 and R1 included), all runtime subtests pass, no ProbeSupport stub.
- Every reject gives exit 1, no stdout and the exact text in the test.
- `cargo test --offline --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` pass.
- `slice6_int_test.py`, `slice6_failure_test.py`, `slice6_constructor_test.py` and the slice 3 to 5 compile-level tests pass. The `payments.beaml` and orders outputs stay byte-identical.

## Exclusions

- Decode of literals and through a constructor (steps 7, 8). The enum only-way-in check (dropped, DL-100).
- Pipes in other expression positions and nested pipes (step 5), except the whole-body clause pipe of decision S4.
- Do not touch `integrations/zed-beaml/`.
