# Slice 6b step 7: REVIEW

Fresh-context REVIEW, 2026-11-07, HEAD `fac6d5ac`. Not a Devil's Advocate. Target: [spec.md](spec.md), plan step 7 and D6B-35 to D6B-40, DL-043, DL-054, DL-062, DL-065, DL-082, DL-102, DL-103, DL-105, [red-review.md](red-review.md), [notes.md](notes.md) GREEN G1 to G9, and `git diff 3a4522b0..HEAD` of `main.rs`, `tests/slice6_decode_test.py` and `slice6/decode/`. TEST evidence: [test-output.log](test-output.log), [test-result.json](test-result.json).

**Verdict: BLOCK (documentation only).** The code meets the step. One Migrate decision is in the code but not in the decision register. Minimum repair: D1 below. No code change.

## Step coverage (observed)

| Plan or spec item | Where | Result |
|---|---|---|
| `effects()` takes a literal enum output field (D6B-35) | `main.rs` `effects()` | met; `slice6_decode_test` 10 OK |
| Literal gives its variant, other String gives the KEEP-VALUE VARIANT, non-String gives `decode` | `__beaml_literal_E` | met; probe A2 below |
| D6B-36 compile error | `keep_variant` | met; test OK |
| D6B-37 span attribute `unknown_fields` | result function `mark` | met; names only |
| D6B-39 compile error | `effects()` | met; two tests OK |
| DL-102 block: count per TYPE, operation and field, first line, MIGRATE STEP help | `--stored` check | met; probes A1, A2 |
| DL-103 `note:` with a count, exit 0 | `Snapshot.notes` | met; probe A1 |
| REPLAY RUN uses the current mapping | `Replay.run/3` | met; test OK |
| Byte guards (`payments.beaml`, orders outputs) | `slice6_struct_order_test`, `run.py` | met |

Nothing beyond need: the own `base64` decoder replaces a new dependency; `__beaml_unknown_fields_<type>` is public because `Replay` is a separate module. No speculative code found.

## Adversarial probes (observed, own script, scratch directory)

Compiler: `target/debug/beaml-spike` of HEAD. A test marker value `zqx-secret-refund` stands in the stored bodies.

**A1. Two environments' worth of records.**

| Source | Records | Exit | stderr |
|---|---|---|---|
| one file, 7 records: `ok`; `pending` kept; marker kept; `7`; `null`; `pending` kept (trace 2); marker kept (trace 2) | mixed | 1 | `error: TYPE Payment: 2 stored RESPONSE RECORDS of operation payments.authorize have no variant of PaymentState for field state` / `record source: ...:4 (line 4)` / help line |
| same file without `7` and `null` | 5 | 0 | `note: TYPE Payment: 2 stored RESPONSE RECORDS of operation payments.authorize kept a value of field state that a literal of PaymentState maps now (DL-103)` |
| two files (first 3 records, last 2 records) | 3 and 2 | 0, 0 | one `note:` each, count 1 each |
| a record whose TYPE name is `Charge` | 4 | 1 | the existing "cannot read" TYPE VERSION text; the DL-102 check does not run (G6 order) |
| two EFFECTS with two output TYPES | - | 1 | `slice 1 supports one effect` (mixed output TYPES cannot occur in 6b) |

- The count per TYPE is right: 2 non-String values, 2 resolved values. Two environments in one file add up; the text has no environment label (spec exclusion).
- When a block and a resolved count both exist for one field, only the block is printed. **[Inference]** Acceptable: the build fails anyway.
- The marker value is absent from stdout and stderr in every case, and absent from `.beaml/actions.jsonl` (10 events, last `{"action":"compile","result":"ok","warnings":0}`).

**A2. Enum output with a KEEP-VALUE VARIANT and an Int wire value.**

- Runtime (stubs of step 7, `elixirc --warnings-as-errors` exit 0): `42`, `4.5`, `:null`, `true` each give `{:error, %BeamlSpike.PaymentError{reason: "decode"}}`, span attribute `reason = "decode"`, no `unknown_fields`. `"ok"` gives `Authorized`. The marker gives `Unknown("zqx-secret-refund")` and `unknown_fields = ["state"]`.
- `--stored` with `ok` and `42`: exit 1, `error: TYPE Payment: 1 stored RESPONSE RECORD of operation payments.authorize has no variant of PaymentState for field state`, `record source: ...:2 (line 2)`, help line. Count 1, singular form (G7).

**A3. Literal enum as an EFFECT INPUT field.**

- `type Order { order_id: String state: PaymentState }` as the EFFECT input: compile exit 0, no stderr. Input only (String output): exit 0.
- The request goes through `ProbeSupport.json(request)`. `:json.encode(%{"s" => {"PaymentState", "Authorized", []}})` raises `{:unsupported_type, {"PaymentState", "Authorized", []}}` (observed). **[Inference]** With the real `ProbeSupport.json` (`:json.encode`, notes.md) the EFFECT call raises at runtime, not a typed failure.
- D6B-40 says this is a compile error. Plan step 7 lists it as an exclusion, and no step of the plan owns it. Not a step 7 defect. See D2.

**A5. DL-103 `note:` text against the actions log.** The note names TYPE, operation, field, enum and a count. No value. The actions log has no note content and no marker value (G9: no event count).

## Consistency of RED, RED review and GREEN

- RED 8 of 8 FAIL for one missing behavior; RED review PASS with N1 to N3. GREEN added N2 and N3 as tests first (RED 2 of 2, then GREEN). Observed in [green-output.log](green-output.log) and rerun in TEST: 10 of 10 OK.
- N1 (a removed literal turns a known value into Unknown, no block, no count) is open as D007 in [decisions-to-be-made](../../../../../wiki/planning/decisions-to-be-made.md). Not changed by GREEN. Correct.
- Fixture hashes: GREEN says equal to RED. The diff `3a4522b0..HEAD -- slice6/decode/` is empty (observed).

## Defects

**D1 (high, process, Migrate; blocks).** The RESPONSE RECORD key `unknown_fields` (S4, G5) changes the stored data contract. notes.md classes it Migrate, open for the OWNER (P2). GREEN wrote it into the generated code and it is committed. It is not in [decisions-to-be-made](../../../../../wiki/planning/decisions-to-be-made.md) and not in the decision log. It also revises D6B-37 ("Over: a new RESPONSE RECORD key"). Consequence: a Migrate choice that the OWNER has not made stands as built fact. DL-105 (step 6) will replace the record contract, so the choice must be visible there. Minimum repair: add an open entry (for example D012, class Migrate, owner OWNER) with the S4 options (key, no key, literals in the `type` key), state that the step 7 code is provisional, and link it from notes.md P2 and D6B-37. No code change.

**D2 (medium, Repair, note).** D6B-40 has no owning step. Probe A3 shows a source that compiles and then raises at runtime. Smallest next test: compile the A3 source and expect the D6B-40 error. Record it in the plan (step 8 or a new mini-step).

**D3 (medium, Migrate, note).** P4: the DL-102 help line asks for a MIGRATE STEP that D6B-39 rejects for this TYPE. A blocked build has no exit in 6b except a store change. This is in notes.md but not in the register. Add it to the D1 entry or its own entry.

## Decisions of this review

- **R1 · Undo.** Verdict BLOCK only on D1, with a documentation-only repair. Alternative: PASS with a note. Reason: the global rule says Migrate decisions stop for the OWNER; a built Migrate choice that the register does not show is a silent decision.
  By: Opus (REVIEW, slice6b-decode-literals)
- **R2 · Undo.** D2 and D3 are notes, not blocks. Reason: D6B-40 is a plan exclusion of step 7; P4 is a documented consequence of two OWNER decisions.
  By: Opus (REVIEW, slice6b-decode-literals)
- **R3 · Undo.** The probes ran in the scratch directory with a test marker value. No fixture or test changed. Reason: the task forbids code and test changes.
  By: Opus (REVIEW, slice6b-decode-literals)
- **R4 · Undo.** Constructor 24 of 25 and decode_ctor 0 of 7 are recorded as expected RED (step 8), not as pass. Reason: the task text.
  By: Opus (REVIEW, slice6b-decode-literals)

## Limits

- The runtime probe uses the step 7 stubs, not a release. `run.py` covers the release path but has no arm with an enum output field (**[Inference]** from the RED review gap list; not checked arm by arm).
- Several environments are only simulated as two files or one mixed file.
