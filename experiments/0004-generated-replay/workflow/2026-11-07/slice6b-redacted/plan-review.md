# PLAN CHECK: slice 6b step 6, `slice6b-redacted`

**[Proposal]** PLAN CHECK, 2026-11-07. Fresh context. Not a Devil's Advocate round. Consequences only.
By: Opus (PLAN CHECK, slice6b-redacted) for every finding and decision in this file (DL-107).
Read: [plan.md](plan.md), [plan.json](plan.json), [decisions.md](decisions.md) (D6B-52 to D6B-71, Q6B-10 to Q6B-12); DL-029, DL-031, DL-032, DL-040, DL-043, DL-055, DL-059, DL-089, DL-102, DL-103, DL-105, DL-106, DL-107 in the [decision log](../../../../../wiki/planning/decision-log.md); [slice 6b plan review](../slice6b-plan/plan-review.md) O1, O2; [step 7 notes](../slice6b-decode-literals/notes.md) S4, G4 to G6; `experiments/0001-syntax-to-beam/src/main.rs` (`stored_version`, `check_stored`, `emit_effect`, `Replay.record`, `body/1`, the replay `expect` chain).
Not read: the GEN copies of the 0003 tests and `run.py` in detail. Findings on them are **[Inference]**.

## Verdict

**BLOCK** on O1 and O2 (high). O3 (high) adds one OWNER question and two test changes. Each fix is a small plan change. No new design is necessary.

## Objections

### O1 · high · A version 1 record passes the build and fails only at replay (D6B-59)

- **[Verified]** `stored_version` (main.rs l. 3273) reads `operation` and the `type` key. It does not read the record key `version`.
- **[Verified]** The enum check of `check_stored` (l. 3355) reads `body_base64`. After 6a it must read `value`.
- **[Inference]** After 6a, a version 1 record with a valid `type` key passes `--stored`. Its REPLAY RUN gives `:body_digest_mismatch`. For an output TYPE without a literal enum field, nothing blocks.
- **Wrong outcome.** A stored record that the build cannot read is ignored at build time. This contradicts DL-031 and DL-040/DL-055: a record without a reader blocks. The reason `body_digest_mismatch` also states tampering, which is false.
- **Smallest test.** 6a P6: `--stored` with one version 1 record of `stored/v1.jsonl` (before conversion) and a correct `type` key. Expect a build error with the line number. Today (inferred): the build passes.
- **Fix in the plan.** D6B-59 adds a `--stored` rule: a record `version` other than `2` is a build error. The replay reason stays as a second guard. Class stays Repair, because the fix follows DL-031.

### O2 · high · An INPUT field that becomes `redacted` does not block, and leaves the value in stored `request` (D6B-66, Q6B-11)

- **[Verified]** The record `type` key and the `--stored` path check hold the EFFECT output TYPE only. The input TYPE has no fingerprint in the record.
- **[Inference]** D6B-66 "a field that becomes redacted blocks a build" is true only for output TYPE fields. The main DL-089 case is an input field (`Order.card_holder`). It changes no stored fingerprint.
- **Wrong outcome.** Old records keep `card_holder` in `request`. The build passes. Every old record gives `:request_mismatch` at replay (plan R3). This is the open case (b) of the slice 6b plan review O1, now silent: stored PII stays, and replay breaks without a build signal (DL-029, DL-031).
- **False pass.** R7 tests only an output field. It shows "becomes redacted blocks", but the input case is not tested.
- **Smallest test.** 6b R8: a stored record with `request: {"order_id": "order-1", "card_holder": "x"}`. The source marks `Order.card_holder` as `redacted`. Expect a build error (count, no value, DL-032). Today (inferred): the build passes.
- **Fix in the plan.** Either the `--stored` check counts stored `request` values under a now-redacted input field and blocks, or Q6B-11 blocks 6b. Q6B-11 must name the input case explicitly. Its options then cover both `request` and `value`.

### O3 · high · The echo test misses one leak path and two channels (R4, D6B-70)

- **Missing case.** The output TYPE declares `card_holder: String` without `redacted`. The service echoes the input. **[Inference]** D6B-54 then puts the MARKER in `value`, and the live result carries it to the host. No compile signal. DL-089 says records never hold the value. The R4 sources (declared redacted, not declared) do not cover this. So a wire value of a redacted field does land in `value` in this case.
- **Channel 1.** **[Verified]** The generated result function calls `:otel_span.set_attribute` for `unknown_keys`, `unknown_fields` and `reason` (main.rs l. 2727, 2731). The step 7 stub keeps these in the process dictionary. The 6b harness list does not name this stub. If it copies the step 7 stub, the OTel attribute channel is never scanned.
- **Channel 2.** The scan finds plain text only. A regression that brings back `body_base64` puts the MARKER in base64. The `run.py` proxy (L2) already does this. A plain scan then passes.
- **Channel 3.** **[Verified]** `unknown_keys` holds key names, nested names dotted (step 8 S8). A service that uses a value as a key puts the value into a name. DL-105 allows names; this is evidence, not a defect.
- **Smallest tests.** R4c: an output TYPE with a plain `card_holder: String` field. Expect either a compile error or a recorded OWNER choice. The `:otel_span.set_attribute` stub appends to a file in the RUN DIRECTORY. The scan also looks for the base64 of the MARKER at the three byte offsets, and for its lower-case hex.
- **Fix in the plan.** Add R4c and the two scan changes. Add an OWNER question for R4c (see Q6B-13 below).

## Raise to Migrate

- **D6B-62 (atom `:redacted` in the field).** DL-105 says "absent and marked". The atom makes the field present with a non-String value in a String field. Host replay code that matches `is_binary` takes another branch than live. That is generated behaviour the OWNER sees. Options: atom in the field; key absent plus the `redacted` list; a typed wrapper.
- **D6B-63 (String-only redacted output).** DL-105 superseded D6B-34 because a compile error forbids a basic feature. D6B-63 adds a compile error for every non-String redacted output field. The OWNER must accept this interim limit.
- **D6B-66 (redacted in the fingerprint).** It replaces D6B-30. The slice 6b plan review O1 classed D6B-30 as Migrate for the same reason (stored records, privacy). Fold it into Q6B-11. It does not renumber records of TYPES without `redacted` (**[Inference]**, the fingerprint text changes only for a redacted field).
- **D6B-59** stays Repair only with the O1 fix. Without the fix it hides a DL-031 decision.

## Checked and consistent

- **D6B-54 `value`.** For a field that is redacted in the newest output TYPE, the wire value never lands in `value` (removed before the digest). Exception: O3 R4c. Wire values of invalid declared fields land in `value`; DL-102 needs them.
- **D6B-66 and DL-102.** A block until a MIGRATE STEP is consistent with DL-102. The block has no exit in 6b. That is stated (Q6B-11).
- **D6B-53, D6B-56, D6B-57, D6B-58, D6B-60, D6B-61, D6B-67 to D6B-71.** No contradiction with DL-089, DL-102, DL-105 found.
- **Sub-step order 6a, 6b, 6c.** Sound. Step 7 GREEN is committed (69b36476). Step 8 GREEN is not yet committed. 6a waits for it (D6B-52). Between 6b and 6c a failure TYPE can copy a redacted value. That is test-only and pre-production.

## OWNER questions

- **Q6B-10.** Options A and B are real. **Missing option C:** LIB stays frozen as its own record version. GEN copies keep their test names. Record-byte lines (`body_length`, `body_sha256`, a1 non-canonical body, body tamper) become "not applicable" rows. The arm comparison then compares outcomes and call counts only. It is cheaper than A (no new meaning for a1) and keeps more than B. **Order note:** Q6B-10 blocks only the GEN copy run and `overlay_diff_test.py`. The 6a RED and GREEN on `slice6_record_test.py` can start before the answer.
- **Q6B-11.** Real options. Must name the input TYPE case (O2) and absorb D6B-66.
- **Q6B-12.** Real options, Answer class correct.
- **Q6B-13 (new, Answer, proposed).** A redacted INPUT field and a same-named plain OUTPUT field of the same EFFECT (O3 R4c). Options: compile error; warning; allowed (the OWNER declares the output plain). Evidence: DL-089 "records never hold the value"; DL-105 protection by the output TYPE.

## First failing tests

- **6a P1.** Genuine: today `version: 1` and `body_base64` exist. A false pass is possible if `value_sha256` is checked against a digest computed by the same Elixir code. P1 must take the digest from Python, as stated. Good.
- **6b R1.** Genuine: the parse fails at `redacted` today. Note: R1 must fail on the wire body, not only on the parse. Otherwise the first GREEN that parses and ignores `redacted` sends `card_holder` and still could pass a parse-only check. The plan asserts the stub body. Good.
- **6b R4.** False pass possible through O3 channels. The positive control and the scan self-check are good.
- **6b R4 expectation.** `unknown_keys` "with `card_holder` and `echo`" conflicts with the dotted names of step 8 S8 (`echo.card_holder`). Fix the expected list before RED.
- **6c F1.** Genuine after 6b. F5 records a limit by name. Good.

## Notes (medium, no block)

- `unknown_fields` is outside `value_sha256` (D6B-58). A changed `unknown_fields` changes the DL-103 resolved count without a digest reject. Step 7 P2 is still an open OWNER question.
- A failing assertion in RED or GREEN prints record text into `red-output.log` or `green-output.log` in the ledger. The MARKER is random test data, so this is not a leak. The scan does not cover it.
- D6B-69 changes fixture hashes of old result directories. Git keeps the old form. Acceptable.

## Decisions in this check

- **PC6R-1 · Repair.** Chose: BLOCK on O1 and O2. Over: pass with notes. Because: both let the build pass while stored records are unreadable or keep PII (DL-031, DL-029). Commits us to: a plan repair before 6a RED.
  By: Opus (PLAN CHECK, slice6b-redacted).
- **PC6R-2 · Repair.** Chose: raise D6B-62, D6B-63, D6B-66 to Migrate. Over: leave them Repair. Because: each changes generated behaviour, syntax or stored-record readability that the OWNER sees.
  By: Opus (PLAN CHECK, slice6b-redacted).
- **PC6R-3 · Undo.** Propose Q6B-13 and option C of Q6B-10. The OWNER decides.
  By: Opus (PLAN CHECK, slice6b-redacted).
- **PC6R-4 · Undo.** Findings on the GEN copies and `run.py` are inferred, not read in detail.
  By: Opus (PLAN CHECK, slice6b-redacted).
