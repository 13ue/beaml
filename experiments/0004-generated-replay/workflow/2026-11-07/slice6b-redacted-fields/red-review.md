# RED review: slice 6b step 6b (`redacted` fields, `with` on EFFECTS, projections, echo scan, stored-value block)

Phase: RED review, 2026-11-07. Base: HEAD 76448b22. Fresh context. Review only: no test, fixture or production file changed. `run.py` not run. No commit.
Inputs: [spec.md](spec.md), [notes.md](notes.md) D6B-148 to D6B-162, [red-output.log](red-output.log), the plan ledger [slice6b-redacted](../slice6b-redacted/plan.md) (plan, repair, D6B-52 to D6B-72, plan check), the [decision log](../../../../../wiki/planning/decision-log.md) DL-059, DL-089, DL-105, DL-111, DL-112, DL-113, DL-115, DL-116, DL-119, DL-125, `tests/slice6_redacted_test.py`, `slice6/redacted/`.

**Verdict: BLOCK** (one high objection, O1). By: Opus (RED review, slice6b-redacted-fields)

## Re-run

- **[Observed]** Scratch build of HEAD (`git archive HEAD experiments/0001-syntax-to-beam`, `cargo build --offline`), passed by `BEAML_SPIKE`. Exit 1, `Ran 17 tests`, `FAILED (failures=21)`. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** 13 methods fail, 4 controls pass. Same set as `red-output.log`. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** Every failure is a parse stop at `redacted`: `expected ':' at byte N` in a `type` field, `expected ','` (enum payload), `expected '->'` (signature), `expected ',' between two MIGRATE CHANGES ...`. No `elixirc`, harness or fixture failure. The three `with` fixtures stop at the `redacted` of the `type` line before the parser reaches `with`; the setup control proves each is valid without both words. Acceptable. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** No MARKER in `red-output.log` or in my run log. The repo tree has no new file from my run. By: Opus (RED review, slice6b-redacted-fields)

## Echo scan (R4, D6B-70, D6B-155)

- **[Observed]** Own plant check with the test's `scan()`: a MARKER planted as a span attribute (`attributes.txt`, inspect form), as an event (decimal byte list), in a record `request` (JSON), in a stderr line (spaced byte list), in a result file (base64 at an offset) and as hex: each one found. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** Not found: upper-case hex and a JSON `\u` escape of the dash. The emitter writes neither. Low, dropped. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** The live span takes `a0` and the REPLAY RUN span takes `p0` (pipe head, the host input). R1, R2 and R4c run a replay that reaches that span, and `assert_channels_clean` checks `spans.txt` for the key `card_holder`. A GREEN that projects only the wire leaves the MARKER in `spans.txt` and fails. No false pass here (DL-119 N2 covered). By: Opus (RED review, slice6b-redacted-fields)
- Channels, by status. By: Opus (RED review, slice6b-redacted-fields)
  - **[Observed]** Covered: span input, `:otel_span.set_attribute/3`, `ProbeSupport.event/2`, `responses.jsonl`, child stdout and stderr, every other file the child writes in the RUN DIRECTORY (crash dump included, cwd is the RUN DIRECTORY), `.beaml/actions.jsonl` of the compile.
  - **[Inference]** Other OTel calls (`set_attributes/2`, `OpenTelemetry.Span.*`): the stubs do not define them, so `elixirc --warnings-as-errors` fails on an undefined remote call. Loud, not a silent gap. Not tested.
  - **[Observed]** `Logger` output goes to the child stdout or stderr, which the scan covers. The release Logger handler and OTel exporter stay out (plan L1).
  - **[Observed]** HTTP stub: `log_message` is silent; requests and responses stay in memory. Never a file.
  - **[Observed]** Elixir child of `--stored`: it runs only for constructor TYPES, its stdout and stderr are never forwarded, `ERL_CRASH_DUMP` is `/dev/null`. The MARKER never enters `--stored`. No channel.
  - **[Observed]** Not covered: the ledger logs (`red-output.log`, later test logs). See O2.
  - **[Observed]** The test posts no job bus event. The MARKER cannot reach the job bus from this test.

## Faithfulness to the decisions

- **[Observed]** DL-111 1A: R4 asserts `type.fields` and the fingerprint with `redacted String` (D6B-148). R7 accepts the fingerprint error beside the D6B-72 head line (D6B-149). Faithful. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** DL-112: no direct-copy case. That is 6c (spec exclusions). No fixture holds a direct copy into a plain field (`prepare` returns the whole `Order`). Correct skip. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** DL-113: R4c builds, `value` keeps the echoed value, the scan finds it only in `responses.jsonl`. Faithful. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** DL-115: R5 expects the atom `:redacted`; D6B-162 expects `decode` without the mark. Faithful. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** DL-116: enum, record, constructor-TYPE field and a String field of a constructor TYPE give the DL-116 text; Int passes DL-116 and meets the slice 1 limit. Neither stricter nor looser. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** D6B-72: R7 (`value`) and R8 (`request`, with and without `with`), count, plural, first line. Top level only; see O1. By: Opus (RED review, slice6b-redacted-fields)

## False-pass checks

- **[Observed]** R1 wire-only GREEN: fails on `spans.txt` (live and replay span) and the scan. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** `with` ignored: "always sent" fails R1 (wire must be `{"order_id"}`); "never sent" fails R2 (wire must hold the MARKER). By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** R8 "count any key": R8b adds a clean line from `stored/v1.jsonl` whose `request` holds `order_id`; any-key counting gives count 3 and first line 1, so it fails. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** The R7/R8 stored value is a distinct token (D6B-150), not a plain word or a path fragment. `rejected()` and `compile()` check stderr and the action events for it. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** D6B-156/157: at HEAD the output decode accepts String, enums with literals and constructor TYPES only (`main.rs` decode loop); a stripped `output_int` gives `slice 1 decodes String fields only, not Payment.attempts`. No Int output decode exists, so no Int accept case is missing. By: Opus (RED review, slice6b-redacted-fields)

## Objections

### O1 · High · No case for a nested redacted INPUT field (projection and D6B-72 "at any depth")

- **[Observed]** Plan "Out of scope": "A nested redacted input field is never sent (D6B-31)". D6B-72: count a redacted key "at any depth of the declared fields". By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** HEAD accepts an EFFECT input with a nested record field (`Order { holder: Holder }`, exit 0). So `Holder { name: redacted String }` inside `Order` is legal input after GREEN. By: Opus (RED review, slice6b-redacted-fields)
- **[Observed]** Every RED fixture puts `redacted` on a top-level input field. No test sends, records, spans or `--stored`-checks a nested one. By: Opus (RED review, slice6b-redacted-fields)
- Consequence: **[Inference]** a GREEN that removes top-level keys only passes all 17 methods and sends the nested value on the wire, into the record `request`, the span input and the stored records, with no `--stored` block. That is the DL-089 leak the step exists to stop. By: Opus (RED review, slice6b-redacted-fields)
- Resolving test: **[Proposal]** one fixture `orders_nested.beaml` (`Order { order_id: String holder: Holder }`, `Holder { name: redacted String }`), run through the R1 flow: wire `{"order_id", "holder": {}}` or the agreed shape, record `request` and spans without `name`, scan clean; plus one R8 case with a stored `request.holder.name` (count 1, P = `request`). If the nested input case is meant to be a compile error instead, record that as a new decision and test the text. By: Opus (RED review, slice6b-redacted-fields)

### O2 · Medium · A failing GREEN or TEST run writes the MARKER into a ledger log

- **[Observed]** These failure messages print the MARKER unredacted: `assertEqual` on the wire dict (R1, R2, control), `assertIn(self.marker.encode(), ...)` (R4, R4c), `assertNotIn("card_holder", spans/events text)` (prints the whole dump), and `done.stdout` in the subtest message (only `stderr` is redacted). By: Opus (RED review, slice6b-redacted-fields)
- Consequence: **[Inference]** a GREEN with one leak writes the MARKER into a committed log; the scan does not cover the ledger logs. The MARKER is a random per-run token, not a secret, so the harm is low, but D6B-70 ("environment variable only") breaks silently. By: Opus (RED review, slice6b-redacted-fields)
- Resolving change: **[Proposal]** pass `msg` with the MARKER replaced by `<M>` and `longMessage = False`, or compare `self.marker in ...` as a boolean. Not a block. By: Opus (RED review, slice6b-redacted-fields)

## Counts

- 17 methods: 13 fail (21 failures with subtests), 4 controls pass. Equal to `red-output.log`. By: Opus (RED review, slice6b-redacted-fields)
- Plant check: 6 of 6 claimed forms found; 2 unclaimed forms missed (low). By: Opus (RED review, slice6b-redacted-fields)

## Limits

- Release path, `run.py` proxy and the real OTel/Logger handlers are not reviewed (plan L1, L2).
- The OTel undefined-call claim is an inference from `--warnings-as-errors`; not run.

## Re-check after repair (edbdfb07)

Phase: RED re-check, 2026-11-07. Base: HEAD edbdfb07. Fresh context. Scope: the repair of O1 and O2 only. Scratch build of HEAD (`git archive HEAD experiments/0001-syntax-to-beam`, `cargo build --offline`), passed by `BEAML_SPIKE`. `run.py` not run. No repo file changed except this section. No commit.
Inputs: [notes.md](notes.md) "RED repair" (D6B-163 to D6B-165), [red-output.log](red-output.log) (last section), `git show edbdfb07` of `tests/slice6_redacted_test.py` and `slice6/redacted/orders_nested.beaml`, DL-105, DL-111, plan D6B-31, D6B-56, D6B-72.

**Verdict: PASS** (no critical or high objection; one medium noted). O1 resolved, O2 resolved. By: Opus (RED re-check, slice6b-redacted-fields)

### Re-run

- **[Observed]** Exit 1, `Ran 19 tests`, `FAILED (failures=23)`. 15 methods fail, the 4 controls pass. Equal to `red-output.log`. By: Opus (RED re-check, slice6b-redacted-fields)
- **[Observed]** `test_N1_nested_redacted_input_field_reaches_no_channel` stops in `build`: `expected ':' at byte 271` (the `redacted` inside `Card`). `test_R8_nested_stored_request_value` gets the same parse error instead of the D6B-72 text. Parse reason only. By: Opus (RED re-check, slice6b-redacted-fields)

### False pass: a GREEN that removes top-level keys only (O1)

- **[Observed]** Simulation in a scratch copy of the test: the N1 flow and the nested `--stored` check run against `orders_nested.beaml` without `redacted`. With no top-level redacted field, this is equal to a GREEN that removes top-level keys only. By: Opus (RED re-check, slice6b-redacted-fields)
- **[Observed]** Each channel fails: By: Opus (RED re-check, slice6b-redacted-fields)
  - wire: `assert_wire` fails (keys `card.holder` present).
  - record `request`: `N1_record_request_has_no_holder` FAIL.
  - replay with the full nested input: `N1_request_with_holder_is_request_mismatch` FAIL (no `:request_mismatch`).
  - span input at depth: `key holder found in spans.txt`.
  - scan: MARKER found in `responses.jsonl` and `spans.txt`.
  - nested R8: the build passes (exit 0), so the D6B-72 count at depth fails.
- **[Observed]** `events.txt` holds no `holder` key in the simulation, so the event check alone does not separate the two GREENs; the scan covers that file. By: Opus (RED re-check, slice6b-redacted-fields)
- **[Inference]** A GREEN that drops the whole `card` record fails `assert_wire` (`card.number` expected). By: Opus (RED re-check, slice6b-redacted-fields)

### Masked failure messages (O2)

- **[Observed]** The simulation failures print labels and key names only. The run log holds no MARKER in plain, hex, base64 or decimal form. By: Opus (RED re-check, slice6b-redacted-fields)
- **[Observed]** A forced case in the scratch copy prints the MARKER from Elixir as plain text, as the inspect of its byte list, as lower-case hex and as base64, then fails. The subtest message shows `<M>` for each form (12 replacements). No MARKER form is in that log. By: Opus (RED re-check, slice6b-redacted-fields)
- **[Observed]** The `assertEqual`, `assertIn` and `assertNotIn` calls on wire, response, span and event data are now `assertTrue` with a label (D6B-165). By: Opus (RED re-check, slice6b-redacted-fields)

### D6B-163 against D6B-56 and D6B-72

- **[Observed]** D6B-72: "a key that is redacted in the input TYPE ... at any depth of the declared fields", "one error per TYPE, operation, field and place". D6B-163 takes T as the EFFECT input TYPE (`Order`) and F as the dotted path `card.holder`. This agrees with the D6B-72 wording and with the D6B-56 dotted name per level. By: Opus (RED re-check, slice6b-redacted-fields)
- **[Observed]** D6B-31: no `with` for a nested field; N1 has no `with` case (D6B-164). Consistent. By: Opus (RED re-check, slice6b-redacted-fields)
- **[Inference]** The help line `redact card.holder` uses a dotted fate path. DL-111 states the `redact f` syntax is a sketch, so this text is a test expectation, not a syntax decision. By: Opus (RED re-check, slice6b-redacted-fields)

### Objections

#### R1 · Medium · The nested R8 does not separate a path-aware count from a leaf-name count

- **[Observed]** The nested stored `request` has one key named `holder`, at `card.holder`. No case has a plain key named `holder` at another path. By: Opus (RED re-check, slice6b-redacted-fields)
- Consequence: **[Inference]** a GREEN that flags every stored key whose leaf name is a redacted field name, at any path, passes. It blocks too much (a loud false block), it does not leak. By: Opus (RED re-check, slice6b-redacted-fields)
- Resolving test: **[Proposal]** add a plain `holder` field to `Order` in a second fixture, or add a stored record whose `request` holds only a top-level plain `holder`; expect no D6B-72 hit for it. Not a block. By: Opus (RED re-check, slice6b-redacted-fields)

### Counts

- 19 methods: 15 fail (23 failures with subtests), 4 controls pass. By: Opus (RED re-check, slice6b-redacted-fields)
- Top-level-only simulation: 6 of 6 nested checks fail (wire, record `request`, replay mismatch, span, scan, nested R8). By: Opus (RED re-check, slice6b-redacted-fields)
- Masking: 4 of 4 forced MARKER forms masked in the Elixir output. By: Opus (RED re-check, slice6b-redacted-fields)

### Limits

- The simulation stands in for a GREEN; no GREEN exists yet.
- Upper-case hex and JSON `\u` escapes stay outside the scan and the mask (low, dropped in the first round).
