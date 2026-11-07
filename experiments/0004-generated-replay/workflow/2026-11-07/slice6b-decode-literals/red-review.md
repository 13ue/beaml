# Slice 6b step 7: RED review

Fresh-context RED REVIEW, 2026-11-07. Not a Devil's Advocate. Target: [spec.md](spec.md), [notes.md](notes.md), [red-output.log](red-output.log), `tests/slice6_decode_test.py`, `slice6/decode/*`.

**Result: PASS. No block.** Three medium notes for GREEN and the OWNER.

## Rerun (observed)

- Baseline: `git archive f74be40c` in a scratch directory, `cargo build --offline`. The live tree was not built. `run.py` was not run.
- Command: `BEAML_SPIKE=<scratch>/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_decode_test.py`.
- Result: 8 tests, 8 FAIL, exit 1. Each failure has the same cause: `effect payments.authorize: slice 1 decodes String fields only, not Payment.state`. This agrees with red-output.log.
- Input hashes agree with notes.md (test file and the four fixture files).
- Fixture check (observed, own script): each record has a correct `body_length`, `body_sha256` and `body_base64`. Each `fingerprint` is the sha256 of `[["order_id","String"],["state","PaymentState"]]` (the `fingerprint()` form of `main.rs`). So the existing TYPE VERSION check does not give a false RED.

## Checks of the classed points

**P1 (D6B-36, follows DL-065).** Confirmed. `test_output_enum_without_keep_value_variant` encodes the compile error. All three fixture enums have `Unknown(String)`. `stored.jsonl` keeps `"refunded"` and the build must pass (exit 0, empty stderr). The block fixture uses `7` and `8` only. **[Inference]** Under D6B-36 a stored String always has a variant, so only a non-String can block. See note N1 for the consequence.

**P2 (record key `unknown_fields`, Repair).** Confirmed for values: the tests assert only `["state"]` or `[]` (names). The block text and the note text are exact matches, so no value can stand in them. Additive: no fixture lacks the key, so this file does not test "a record without the key counts as `[]`". **[Inference]** This is low risk: enum output fields are new in this step, so no old enum record exists. Old String-only snapshots (`stored/v1.jsonl` and others) have no key, and the other step files and `run.py` use them. A GREEN that needs the key everywhere fails there.

**P4 (no way out inside 6b).** The block text does not name `quarantine` or `retire`. It asks for "a MIGRATE STEP to a new TYPE VERSION of Payment". That form exists in general, but for this TYPE it gives the D6B-39 error. So the help line points to a dead end in 6b. This agrees with the documented limit P4. No test fault.

## Partial GREEN (inference from the test code)

| Partial GREEN | Tests that still fail |
|---|---|
| Decode, no `--stored` check | `test_stored_value_without_a_variant_blocks`, `test_resolved_unknown_reports_the_count` |
| `--stored` check reads only `unknown_fields`, no body decode | `test_resolved_unknown_reports_the_count` (count 2, not 1), `test_stored_value_without_a_variant_blocks` |
| No `unknown_fields` key from the writer | `test_runtime_live_decode` (2 subtests) |
| No span attribute | `test_runtime_live_decode`, `test_runtime_replay` |
| No D6B-36 or no D6B-39 check | the matching reject test |

`test_stored_values_all_resolve` passes with decode only. That is correct: it is the accept case. A missing or crashed runtime case gives FAIL (result `None`), not a pass.

## Replay and DL-102

- `replay_resolved_uses_current_mapping` replays a record with `"pending"` and `unknown_fields = ["state"]`. The expected result is `Pending`. This proves that the REPLAY RUN ignores the write-time flag and uses the current mapping.
- **[Limit]** The "old mapping" is hand-built. No build without `Pending` wrote the record. See N2.

## `note:` format

- The DL-103 line names TYPE, operation, field, enum and the count. No value. Exact match, one line.
- Environment: one `--stored` file is one environment (spec exclusion). The text has no environment label. Accepted limit.

## Notes (max three, all medium, no block)

**N1 (medium, OWNER question, Migrate).** Under P1 a literal removal or a change of a literal String gives no block and no count. Example: remove `Pending = "pending"`. Old records then replay as `Unknown("pending")`, not `Pending`. DL-102 names "a changed enum mapping" as a trigger. DL-103 covers only Unknown to known, and its limit names only known to known. Known to Unknown has no rule. Wrong outcome: a deploy changes the replay result of stored records with no step and no report. Smallest test: `stored.jsonl` with the `"pending"` record, a source without `Pending`; record the expected exit and stderr after the OWNER decides. This is not a RED fault. The step tests encode no answer.

**N2 (medium, GREEN).** The stub `ProbeSupport.Capture.write/2` keeps the record as an Elixir map, and the test reads `.unknown_fields` (an atom key). The `--stored` check reads the JSON key `"unknown_fields"`. No test writes a record through the real JSON path and reads it back with the check. Wrong outcome: writer and check disagree on the key, and DL-103 counts stay 0 in real runs. Smallest test: compile a source without `Pending`, capture a `"pending"` response through the real JSON encode, then build `orders.beaml` with that line as `--stored`. Expect the DL-103 note with count 1.

**N3 (medium, GREEN).** Value absence is checked only where the test asserts exactly (the `unknown_fields` attribute, the block and note texts, the captured key). Other span attributes, the action events and other record keys are not checked for `"refunded"`. Wrong outcome: a GREEN that adds a decoded value to another attribute or key passes. Smallest test: in the live case, assert that no stored attribute value and no captured record key except `body_base64` contains `"refunded"`, and that `.beaml/actions.jsonl` does not contain it.

## Other gaps (already in notes.md, unchanged)

- A missing enum key or `null` in a stored body: no block test.
- Several TYPES or fields in one report: not tested.
- The real release path: `run.py` at TEST. **[Unknown]** whether `run.py` has an arm with an enum output field.

## Limits of this review

- Read-only review. No production file or test changed.
- The partial-GREEN table is reasoning from the test code, not runs of partial builds.
