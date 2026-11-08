# Spec: slice 6b step 6b, `redacted` on fields, `with` on EFFECTS, projections, marked fields, echo test, stored-value block

**[Proposal]** Solve / RED, 2026-11-07. Base: HEAD 050d6801. Plan ledger: [slice6b-redacted](../slice6b-redacted/plan.md) (sub-step 6b, "Plan repair"), [decisions](../slice6b-redacted/decisions.md) D6B-52 to D6B-72, [plan check](../slice6b-redacted/plan-review.md).
OWNER answers: DL-059, DL-089, DL-105, DL-111, DL-112, DL-113, DL-115, DL-116, DL-125 in the [decision log](../../../../../wiki/planning/decision-log.md). New defaults D6B-148 to D6B-162: [notes.md](notes.md).
Test: `tests/slice6_redacted_test.py`. Fixtures: `slice6/redacted/`. Run: [red-output.log](red-output.log).
By: Opus (RED, slice6b-redacted-fields).

## Contract

### Syntax

- `name: redacted TYPE` stands only in a `type` field (D6B-29). In an enum payload, a signature line or a MIGRATE CHANGE it is a compile error: `error: redacted stands only before a field TYPE in a type (D6B-29)` (D6B-64).
- `with f1, f2` stands after the `)` of the EFFECT target (D6B-31). Each name is a top-level redacted field of the EFFECT input TYPE T. Errors (D6B-65): `error: with names F, which is not a field of T`; `error: with names F, which is not a redacted field of T`; `error: with names F twice`.
- D6B-153: for D6B-64 and D6B-65 the first stderr line is exact. A later `  at byte N` line is allowed.

### Projections (DL-089, D6B-32, D6B-33)

- Wire body: the input without every redacted field, except the `with` names.
- Record `request`, the `:request_mismatch` compare, the span input argument and `ProbeSupport.event`: the input without every redacted field, `with` names included. The key is removed; no placeholder.

### EFFECT output (DL-105, DL-115, DL-116, DL-113)

- A redacted output field: the live decode returns the real value to the flow. The record `value` does not hold the field. `redacted` lists it when it was present and valid (D6B-55). `unknown_keys` holds dotted names per level, also below an undeclared key (D6B-56 amendment).
- The record `type` key and the fingerprint write the field TYPE text `redacted String` (D6B-148, from DL-111 option 1A and the D6B-66 text).
- A REPLAY RUN puts the atom `:redacted` into each field of the `redacted` list (DL-115). A record whose `redacted` list lacks the field replays as the typed reject `decode` (D6B-55).
- DL-116 interim: a redacted output field that is not a String or Int field of a TYPE without a constructor is a compile error. Each nested level stands for itself. Text (D6B-154):
  `error: effect E: the redacted field T.F must be a String or Int field of a TYPE without a constructor in slice 6b (DL-116)` and `  help: remove redacted from T.F; the limit holds until a rule over an absent value exists (DL-116)`.
- The DL-116 check comes before the slice 1 decode limit (D6B-157). A redacted Int output field passes DL-116; the existing slice 1 decode limit still rejects it (D6B-156).
- DL-113: a plain output field with the same name as a redacted input field is allowed. The record `value` holds its value.

### Stored-value block (D6B-72, DL-111, D6B-151, D6B-152)

- `--stored` counts the records whose `request` holds a key that is redacted in the EFFECT input TYPE (P = `request`), and whose `value` holds a key that is redacted in the output TYPE (P = `value`). One error per TYPE, operation, field and place:

```
error: TYPE T: N stored RESPONSE RECORD[S] of operation OP hold[s] a value of the redacted field F in P
  record source: S:L (line L)
  help: declare the fate in a MIGRATE STEP: redact F (DL-111); slice 6b has no form for it yet (DL-125)
```

- One record: `RECORD ... holds`; more: `RECORDS ... hold` (D6B-151). L is the first hit line. No stored value byte in stderr (DL-032).
- A stored output record with the old fingerprint (plain `card_holder: String`) also gets this head line. The DL-111 1A fingerprint error may show too (D6B-149).

## Tests (`tests/slice6_redacted_test.py`)

| Test | Plan case | Source | Asserts |
|---|---|---|---|
| `test_R1_no_with_never_sends_the_redacted_field` | R1 (first RED), R3 | `orders.beaml` | wire body `{"order_id"}`; record `request` without card_holder; span and event dumps exist without card_holder; replay; full-input `request` is `:request_mismatch`; scan clean |
| `test_R2_R3_with_sends_the_field_on_the_wire_only` | R2, R3 | `orders_with.beaml` | wire body has the MARKER; record, span, event without it; projected `request` replays; full-input `request` is `:request_mismatch` (D6B-160); scan clean |
| `test_R4_R5_echo_into_a_declared_redacted_output_field` | R4, R5 | `echo_declared.beaml` | positive controls; live gets the value; `value`, `redacted: ["card_holder"]`, `unknown_keys: ["echo", "echo.card_holder", "echo.order_id"]`, Python digest, `type` fields and fingerprint (D6B-148); replay `:redacted`; no mark gives `decode` (D6B-162); scan clean |
| `test_R4_echo_into_an_output_type_without_the_field` | R4 | `orders_with.beaml` (D6B-158) | `redacted: []`, `unknown_keys: ["card_holder", "echo", "echo.card_holder", "echo.order_id"]`; scan clean |
| `test_R4c_same_named_plain_output_field_keeps_the_value` | R4c (DL-113) | `echo_plain.beaml` | live and replay give the value; the scan finds the MARKER only in `responses.jsonl`, plain form |
| `test_R6_redacted_outside_a_type_field` | R6 (D6B-64) | `bad/enum_payload`, `signature`, `migrate_change` | first line exact |
| `test_R6_with_rejects` | R6 (D6B-65) | `bad/with_unknown`, `with_plain`, `with_twice` | first line exact |
| `test_R6_dl116_interim_limit` | R6 (DL-116) | `bad/output_enum`, `output_record`, `output_constructor_field`, `output_constructor_type` | exact two-line text |
| `test_R6_redacted_int_output_passes_dl116` | R6 (DL-116 Int) | `bad/output_int` | exact slice 1 decode limit text, not DL-116 (D6B-156) |
| `test_R7_stored_output_value_under_a_field_that_is_now_redacted` | R7 | `output_redacted.beaml` + `stored-unredacted.jsonl` | exit 1; D6B-72 head line with P = `value`; no stored value byte (D6B-149) |
| `test_R7_stored_value_with_the_redacted_fingerprint_gets_the_exact_block` | R7 | same, record `type` rewritten to the D6B-148 fingerprint | exact D6B-72 text |
| `test_R8_stored_request_value_of_a_now_redacted_input_field` | R8 | `orders.beaml`, `orders_with.beaml` + `stored-request-unredacted.jsonl` | exact D6B-72 text, P = `request`, count 1 (D6B-161) |
| `test_R8_count_and_first_line` | R8 | `orders.beaml` + clean line, two hit lines | count 2, first line 2, plural |
| `test_control_plain_input_leaks_and_the_scan_finds_it` | control (D6B-155) | `control.beaml` | passes today: the scan finds a real leak in `responses.jsonl` and `spans.txt` |
| `test_scan_finds_each_planted_form` | scan self-check (D6B-70) | none | each form in a planted file, base64 at offsets 0, 1, 2 of real encodings, clean file gives no hit |
| `test_R6_fixtures_build_without_redacted_and_with` | setup control | `bad/*` without `redacted` and `with` | passes today |
| `test_R7_R8_fixtures_build_without_redacted` | setup control | `output_plain`, `control` + the stored fixtures | passes today |

Harness: file-backed stubs (`ProbeSupport.span/5`, `event/2`, `:otel_span.set_attribute/3`, `ProbeSupport.Capture.write/2`), real `ProbeSupport.json/1`, port and MARKER by environment variable, a Python loopback HTTP stub with memory. The RUN DIRECTORY holds the generated module, the stubs, the beams, `checks.exs`, stdout, stderr, `responses.jsonl`, `spans.txt`, `events.txt`, `attributes.txt`. The scan covers these and `.beaml/actions.jsonl` of the compile.

## Acceptance (GREEN)

- Every test of `tests/slice6_redacted_test.py` passes with the HEAD compiler build.
- The four control tests keep passing.
- The existing checks of plan "Checks, every sub-step" pass. Sources without `redacted` and `with` give byte-equal output.

## Exclusions and limits

- No accept case for a redacted nested output field: a plain nested record output field fails the slice 1 decode limit, and a nested TYPE with a constructor is a DL-116 reject. So "nested allowed" (DL-116) has no runtime test in 6b (D6B-156).
- `redact f` (DL-111 2A, DL-125) has no syntax yet. The block has no exit in 6b.
- The derived-value rule and the direct-copy rule (DL-112) are 6c.
- Release path (real ProbeSupport, Logger handler, OTel exporter): plan limit L1. `run.py` not run.
- The grammar corpus line `drop secret: redacted String` (forms.txt) parses in the grammar; the compiler rejects it by D6B-64. No grammar change in this step.

### Docs additions (2026-11-07, after the TEST re-check of acf12d75)

By: Opus (docs slice6b/6c). The lines above stay as the RED record.

- **[Verified]** Correction of the line "a nested TYPE with a constructor is a DL-116 reject": the review repair (D6B-184) rejects two forms. (1) A redacted field below an enum payload (`Payment.pay` holds an enum whose payload TYPE `Holder` has the redacted `name`). (2) A redacted field below a TYPE with a constructor (`Amount` has a constructor; `Inner.s` is redacted). Both give the DL-116 interim text, exit 1, no stdout. Fixtures: `bad/output_enum_payload.beaml`, `bad/output_constructor_above.beaml`.
- **[Verified]** D6B-184 wording limit: the DL-116 text names the field (`Holder.name`, `Inner.s`), not the enum or the constructor TYPE above it. Its clause "a TYPE without a constructor" does not describe these two cases: `Holder` and `Inner` have no constructor. The text gives no reason for the reject. The help line ("remove redacted from T.F") is correct. A new text is a later choice.
- **[Verified]** D6B-31 form: `with` takes top-level names only. A dotted name (`with card.holder`) is a parse error, `expected identifier at byte N`, not a named rule text (observed with the HEAD build 5b7feb92).
