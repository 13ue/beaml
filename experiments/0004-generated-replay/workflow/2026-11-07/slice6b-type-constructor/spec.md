# Slice 6b step 3: the record constructor and pure pipes without spans

Step: [plan.md, Step 3](../slice6b-plan/plan.md#step-3-record-constructor-slice6b-type-constructor), `plan.json` step `type-constructor`.
Decisions: [D6B-11 to D6B-19, D6B-28](../slice6b-plan/decisions.md). Decision log: DL-092, DL-093 in [decision-log.md](../../../../../wiki/planning/decision-log.md).
Review notes: [plan-review.md](../slice6b-plan/plan-review.md) (2) move D6B-28 to step 3, (5) assert the exact text.

## Contract

- A `fn` with an uppercase name is a constructor. Its name must be a declared `type`, and its output must be that TYPE (D6B-11). Enum constructors come in step 4.
- A `fn` line without `=` is a signature line with `name: TYPE` parameters only. The clauses below take its TYPES by position. A clause annotation must equal the signature TYPE (D6B-12).
- When a name has a signature line, a clause before it is an error (D6B-13). Without a signature line, each clause types its own parameters (today's rule).
- In step 3 a constructor has one signature. A second equal signature line is `unreachable signature` (D6B-23 text, step 4 keeps it).
- Each constructor compiles to `def new_<TYPE>_1(a0)` with the validity wrapper and private clauses `__beaml_new_<TYPE>_1` (D6B-15). A pipe step `|> T` calls it.
- A TYPE with a constructor is nominal: `same_type` is name equality when either side has a constructor (D6B-17).
- The record literal `T { ... }` of such a TYPE is legal only in its own constructor clauses. Record patterns stay legal everywhere (D6B-18).
- Such a TYPE is rejected as EFFECT input, output, failure TYPE and as a field of one (D6B-19, interim for Q6B-3).
- D6B-28, spans part: only a whole-body pipe with an EFFECT step emits `ProbeSupport.span`. Every other pipe is plain calls (a `with` for failing steps).
- Exact texts: see [notes.md](notes.md), decisions S8 to S12.

## Pass rule

- `python3 -B experiments/0004-generated-replay/tests/slice6_constructor_test.py`: 25 of 25 pass (20 RED plus 5 RED repair), all runtime subtests pass, no ProbeSupport stub.
- Every reject gives exit 1, no stdout and the exact text in the test.
- `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` pass.
- `slice6_int_test.py`, `slice6_failure_test.py` and the slice 3 to 5 compile-level tests pass. The `payments.beaml` and orders outputs stay byte-identical.

## Exclusions

- Enum constructors, several signatures (step 4). Nested pipes and the one-clause part of D6B-28 (step 5). Decode through a constructor (Q6B-3).
- Do not touch `integrations/zed-beaml/`.
