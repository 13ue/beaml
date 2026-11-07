# Slice 6b step 8: spec

**[Proposal]** SOLVE / RED phase, 2026-11-07. Step 8 of [the slice 6b plan](../slice6b-plan/plan.md). Decisions of this phase: [notes.md](notes.md). Shared forms with step 7: [../slice6b-decode-literals/spec.md](../slice6b-decode-literals/spec.md).

## Goal

The generated decode reads an EFFECT output field whose TYPE has a constructor. An enum constructor maps the field value to a variant. A record constructor checks the field value. The `--stored` check runs the constructors over the stored RESPONSE RECORDS.

## Sources of the rules

- DL-084 K1: the parameter names of a signature line are the keys.
- DL-085: signatures are tried top to bottom. The first match wins.
- DL-099 B: the keys are inside the field's own value. A one-parameter signature reads the field value directly.
- DL-101 A: the decode calls the record constructor. Its failure is a typed reject. It replaces D6B-19 (interim).
- DL-102: a stored record that fails a constructor blocks the build. Counts and reasons, never values.
- DL-065, D6B-50: the keep-value check on the last clause of each signature of an enum constructor in an EFFECT decode.
- D6B-48: a signature matches when all its keys are present and each value is valid for its TYPE. No match is the typed reject `decode`.
- D6B-49: `unknown_keys` inside the field value treats every parameter name of every signature as declared.
- Step 7 S4, S5 (open): the record key `unknown_fields` and the DL-102 block lines.

## Behavior under test

| Case | Field value | Expected |
|---|---|---|
| Signature 1 | `"state": {"status":"ok","decline_reason":""}` | `Authorized` |
| Signature 1, pipe clause | `{"status":"declined","decline_reason":"card"}` | `Declined(DeclineReason { text: "card" })` |
| Signature 1, last clause | `{"status":"refunded","decline_reason":""}` | `Unknown("refunded")`, `unknown_fields = ["state"]` (span attribute and record key) |
| Signature 2 (one parameter) | `"state": "ok"` | `Authorized` |
| No match | wrong TYPE, missing key, Int | typed reject `decode` |
| Two object signatures share a key (DL-085) | `{status, decline_reason, code}` | the variant of signature 1 (`SHARED` source) |
| Same source, signature 2 only | `{status, code}` | the variant of signature 2 |
| Record constructor accepts | `"amount": {"value":"12.50","currency":"EUR"}` | the Amount value |
| Record constructor fails | `{"value":"1","currency":""}` | typed reject `constructor` (S6, Repair, R4) |
| Record constructor, missing key | `{"value":"1"}` | typed reject `decode` |
| Stray key | `state` with keys `code` and `extra` | `unknown_keys = ["state.extra"]` (S8) |
| REPLAY RUN | stored records 2 and 3 | `Declined(...)`, `Pending` |
| `--stored` | every record passes | exit 0, empty stderr |
| `--stored` | 2 records fail `Amount` | exit 1, count, failure TYPE, first line, MIGRATE STEP help (S9) |
| `--stored` | 1 record matches no signature | exit 1, same form (S9) |
| Compile | last clause `_, _ -> Pending` | D6B-50 error (S10) |

## Exclusions

- A constructor on the EFFECT output TYPE itself (the flat body of DL-099), on the input TYPE and on a failure TYPE. D6B-19 stays there (S3).
- Int parameters in a decode signature. EFFECT outputs decode String fields only (S4). A constructor TYPE with an Int parameter in an output field gets the slice 1 text `slice 1 decodes String fields only, not T.F` (R3).
- DL-103 counts for a constructor clause that maps a kept value now (S11).
- MIGRATE STEP forms `quarantine` and `retire` (DL-102 sketch).
- Lists as an external return TYPE (DL-084 "later").

## Files

- Fixture: `experiments/0004-generated-replay/slice6/decode-ctor/orders.beaml`.
- RECORD SNAPSHOTS: `slice6/decode-ctor/stored.jsonl`, `stored-fail.jsonl`, `stored-nomatch.jsonl` (hand-built, fingerprint by D6B-38).
- Test: `experiments/0004-generated-replay/tests/slice6_decode_ctor_test.py`. 7 tests (RED repair: 7 of 7 FAIL).
- Changed step 3 test: `tests/slice6_constructor_test.py` `test_constructor_type_in_an_effect_output_field` expects `effect payments.authorize: slice 1 decodes String fields only, not P.n` (notes.md R3). Every other step 3 test stays.
- Depends on: [../slice6b-struct-order/](../slice6b-struct-order/) GREEN (notes.md R5).
