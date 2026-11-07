# Slice 6b step 7: spec

**[Proposal]** SOLVE / RED phase, 2026-11-07. Step 7 of [the slice 6b plan](../slice6b-plan/plan.md). Decisions of this phase: [notes.md](notes.md).

## Goal

The generated decode reads an EFFECT output field whose TYPE is an enum with ENUM LITERALS. The `--stored` check runs the current mapping over the stored RESPONSE RECORDS.

## Sources of the rules

- DL-082 L: ENUM LITERALS map a String 1:1 to a variant.
- DL-062, DL-065: `Unknown(String)` is a declared variant. The decode of outside data keeps the value.
- D6B-35: the field reads its own key. A literal gives its variant. Another String gives the keep-value variant. A non-String gives the typed reject `decode`.
- D6B-36: an enum field in an EFFECT output needs a keep-value variant. Else a compile error.
- D6B-37: a keep-value decode sets the span attribute `unknown_fields` (field names, no values).
- D6B-38 "count only": superseded by DL-102. The fingerprint part (enum name only, no literals) stays.
- D6B-39: an enum field in an EFFECT output TYPE with a MIGRATE CHAIN or a VERSION MARK is a compile error in 6b.
- DL-102: a stored record that fails the current mapping blocks the build. The message gives counts and reasons, never values. The help line asks for a MIGRATE STEP. A REPLAY RUN uses the current mapping.
- DL-103: a stored record whose kept value a new literal maps now is a count, no block.

## Behavior under test

| Case | Input | Expected |
|---|---|---|
| Live decode | `"state": "ok"` | `Authorized` |
| Live decode | `"state": "refunded"` | `Unknown("refunded")`, span attribute `unknown_fields = ["state"]` |
| Live decode | `"state": 7` or `null` | typed reject `decode` |
| RESPONSE RECORD | kept value | key `unknown_fields = ["state"]` (notes.md S4, open) |
| `--stored` | every value maps | exit 0, no report |
| `--stored` | a record kept at write time, a literal maps it now | exit 0, one `note:` line with the count (DL-103) |
| `--stored` | values that no variant takes | exit 1, count per TYPE and field, first line, MIGRATE STEP help (DL-102) |
| REPLAY RUN | old kept record, value now a literal | current mapping: `Pending` |
| Compile | output enum without keep-value variant | D6B-36 error |
| Compile | output enum field in a TYPE with a chain or a mark | D6B-39 error |

## Exclusions

- MIGRATE STEP forms `quarantine` and `retire` for a TYPE VERSION (DL-102 sketch). This step only blocks and reports.
- Enum fields in EFFECT inputs (D6B-40), in nested records and in lists.
- Decode through an enum constructor (step 8).
- A value that moves from one known variant to another (DL-103 limit).
- Several environments: one `--stored` file is one environment.

## Files

- Fixture: `experiments/0004-generated-replay/slice6/decode/orders.beaml`.
- RECORD SNAPSHOTS: `slice6/decode/stored.jsonl`, `stored-resolved.jsonl`, `stored-fail.jsonl` (hand-built, fingerprint by D6B-38).
- Test: `experiments/0004-generated-replay/tests/slice6_decode_test.py`.
