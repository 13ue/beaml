# Notes: slice 6b step 6b (`redacted` on fields, `with` on EFFECTS)

Phase: Solve / RED, 2026-11-07. Base: HEAD 050d6801. No production file changed. `run.py` not run. No commit.
Inputs: [plan.md](../slice6b-redacted/plan.md) incl. "Plan repair", [plan.json](../slice6b-redacted/plan.json), [decisions.md](../slice6b-redacted/decisions.md) D6B-52 to D6B-72, [plan-review.md](../slice6b-redacted/plan-review.md); DL-059, DL-089, DL-105, DL-106, DL-111, DL-112, DL-113, DL-115, DL-116, DL-117, DL-119, DL-120, DL-125; the step 6a ledger [slice6b-records-v2](../slice6b-records-v2/spec.md).
Proposals: the plan ledger has no `proposal-ultra.md` or `proposal-lite.md` for 6b. The RED follows the plan test list R1 to R8 directly.
Test: `tests/slice6_redacted_test.py`. Fixtures: `slice6/redacted/`. Contract: [spec.md](spec.md). Run: [red-output.log](red-output.log).
Compiler: scratch build of HEAD (`git archive HEAD experiments/0001-syntax-to-beam`), passed through `BEAML_SPIKE`.

## RED result

- **[Observed]** 17 test methods. Exit 1, `FAILED (failures=21)` (subtests counted).
- **[Observed]** 13 test methods fail, 4 pass. The 4 passes are controls: `test_control_plain_input_leaks_and_the_scan_finds_it`, `test_scan_finds_each_planted_form`, `test_R6_fixtures_build_without_redacted_and_with`, `test_R7_R8_fixtures_build_without_redacted`.
- Failure reasons, every one a missing behaviour:
  - The parser stops at `redacted` in a `type` field: `expected ':' at byte N` (R1, R2, R4, R4c, R5, R6 with and DL-116 cases, R7, R8).
  - The parser stops at `redacted` in an enum payload (`expected ','`), a signature line (`expected '->'`) and a MIGRATE CHANGE (`expected ',' between two MIGRATE CHANGES ...`) (R6, D6B-64).
- No setup failure:
  - The controls show that each fixture is valid without `redacted` and `with`, and that the stored fixtures build against the plain sources.
  - The runtime harness runs end to end today on `control.beaml`: build, `elixirc --warnings-as-errors`, stub, live call, record, REPLAY RUN, scan.
  - A scratch check ran every runtime case set against `control.beaml`. Each case printed PASS or FAIL, so `checks.exs` has no Elixir syntax error. That check is a scratch script, not part of the test.
- **[Observed]** No MARKER in `red-output.log`. Failure messages replace the MARKER with `<M>`.

## Decisions

### Undo

- D6B-150 · Undo · The stored value of R7 and R8 is `STORED-HOLDER-3e9d1c`, not `x`. Reason: `x` is in the path `experiments`, so a stderr byte check for it means nothing. By: Opus (RED, slice6b-redacted-fields)
- D6B-151 · Undo · D6B-72 text: one record gives `RECORD ... holds`, more give `RECORDS ... hold`, as the other `--stored` texts. By: Opus (RED, slice6b-redacted-fields)
- D6B-153 · Undo · D6B-64 and D6B-65: the first stderr line is exact; a later `  at byte N` line is allowed. Reason: these are parse-level errors, and the parser adds a location today. By: Opus (RED, slice6b-redacted-fields)
- D6B-154 · Undo · DL-116 text: `error: effect E: the redacted field T.F must be a String or Int field of a TYPE without a constructor in slice 6b (DL-116)` and `  help: remove redacted from T.F; the limit holds until a rule over an absent value exists (DL-116)`. Reason: the Q6B-15 option A text, widened to Int (DL-116), in the D6B-39 style with the EFFECT name; DL-116 asks for a slice-limit text with a help line. By: Opus (RED, slice6b-redacted-fields)
- D6B-155 · Undo · The scan also looks for the decimal byte list of the MARKER (`77,65,...` and `77, 65, ...`), the form of the emitter. A control source with a plain `card_holder` shows that the scan finds a real leak. By: Opus (RED, slice6b-redacted-fields)
- D6B-158 · Undo · Fixture names use underscores (`orders_with`, `echo_declared`, `echo_plain`, `output_plain`, `output_redacted`), not the plan's hyphens. Reason: the compiler requires a lowercase identifier as the file name of a source with an EFFECT (span names). `orders_with.beaml` is also the R4 source whose output TYPE does not declare `card_holder`; a separate `orders-echo-undeclared.beaml` would be the same file. By: Opus (RED, slice6b-redacted-fields)
- D6B-159 · Undo · The fixtures use `fn prepare order: Order -> Order = order` before the EFFECT. Reason: the D6B-89 Orders event then fires, so the event channel is not empty; the step does not read the redacted field (DL-115). By: Opus (RED, slice6b-redacted-fields)
- D6B-161 · Undo · R8 also runs `orders_with.beaml` (a `with` name is removed from `request` too, D6B-32). R8b puts a clean record on line 1 and two hits on lines 2 and 3: count 2, first line 2. By: Opus (RED, slice6b-redacted-fields)
- D6B-162 · Undo · R5 "record without the mark": `redacted: []` and the Python digest of the same `value`. Expected: the typed reject `decode`. By: Opus (RED, slice6b-redacted-fields)

### Repair

- D6B-148 · Repair · The TYPE text of a redacted field in the record `type` key and in the fingerprint is `redacted String`. Chose: the D6B-66 text. Over: another spelling. Because: DL-111 takes option 1A ("a field that becomes redacted is a new TYPE VERSION"), and D6B-66 is the text of 1A. Commits us to: R4 asserts the fields and the fingerprint; R7b builds a record with this fingerprint. By: Opus (RED, slice6b-redacted-fields)
- D6B-149 · Repair · R7 with the old fingerprint asserts exit 1, the D6B-72 head line with P = `value`, and no stored value byte. The DL-111 1A fingerprint error may also show, before or after. Chose: the head line as a required line. Over: the exact text, or the fingerprint error only. Because: D6B-72 holds under every Q6B-11 option; the exact text is tested in R7b, where the fingerprint matches. Commits us to: GREEN reports D6B-72 also when the fingerprint check fails. By: Opus (RED, slice6b-redacted-fields)
- D6B-152 · Repair · The D6B-72 help line is `  help: declare the fate in a MIGRATE STEP: redact F (DL-111); slice 6b has no form for it yet (DL-125)`. Chose: the decided exit. Over: the plan text "their fate is an OWNER decision (Q6B-11)". Because: Q6B-11 is decided (DL-111 2A); DL-125 makes `redact f` a fate operation without syntax yet. Commits us to: the help line changes when the `redact` form lands. By: Opus (RED, slice6b-redacted-fields)
- D6B-156 · Repair · A redacted Int output field passes DL-116; the RED expects the existing text `effect payments.authorize: slice 1 decodes String fields only, not Payment.attempts`. Chose: pin the decode limit. Over: an accept test that runs an Int field. Because: the decode of Int and of plain nested record output fields does not exist today, so DL-116 "Int" and "nested allowed" have no runtime case in 6b. Commits us to: a later step adds the Int and nested accept cases. By: Opus (RED, slice6b-redacted-fields)
- D6B-157 · Repair · The DL-116 check comes before the slice 1 decode limit. Chose: `holder: redacted Holder` gives the DL-116 text. Over: the decode limit text. Because: the DL-116 text names the real limit and the help; the decode limit would hide it. Commits us to: GREEN orders the two checks. By: Opus (RED, slice6b-redacted-fields)
- D6B-160 · Repair · R3 stores the full host input (with the MARKER) as `request` for the `:request_mismatch` case. Chose: the real input. Over: another value of `card_holder`. Because: a GREEN that compares the full input would match it and fail the case; another value would mismatch under both readings (false pass). Commits us to: the MARKER is in this record in memory only; it is never written. By: Opus (RED, slice6b-redacted-fields)

### Taken from decided answers (no new default)

- DL-113 (Q6B-13 C): R4c passes when the build passes and the record `value` holds the echoed value. The scan then finds the MARKER in `responses.jsonl` only.
- DL-115 (Q6B-14 A): R5 expects the atom `:redacted` in the field.
- DL-116 (Q6B-15 A): R6 rejects enum, record and constructor-TYPE fields and fields of a TYPE with a constructor.
- DL-111 (Q6B-11 1A + 2A) and DL-125: see D6B-148, D6B-149, D6B-152.

## Deferred edits

- None. No existing assertion changes. `slice6_record_test.py` P1 (`redacted: []`) stays true for sources without `redacted`.

## Limits

- The test imports `arm_tree`, `slice6_failure_test` (RUNTIME_HEAD, RUNTIME_TAIL, EMPTY_STORED), `slice6_record_test` (`ex`) and `stored_types_test` (`value_sha256`). It has its own `compiler()` and `build`.
- The harness is release-free (plan L1). Trace and span ids are empty strings in the stubs.
- The scan does not cover the ledger logs. They hold no MARKER (observed for this RED run).
