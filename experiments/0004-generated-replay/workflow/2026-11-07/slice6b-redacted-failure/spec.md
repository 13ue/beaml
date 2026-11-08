# Spec: slice 6b step 6c, no non-redacted copy of a redacted value

**[Proposal]** Solve / RED, 2026-11-07. Base: HEAD 461d024e. Plan ledger: [slice6b-redacted](../slice6b-redacted/plan.md) ("Failure TYPE rule (6c)", "6c"), [decisions](../slice6b-redacted/decisions.md) D6B-67.
OWNER answers: DL-105, DL-112 (Q6B-12 A, the rule holds everywhere), DL-113 (Q6B-13 C) in the [decision log](../../../../../wiki/planning/decision-log.md). New defaults D6B-174 to D6B-183 (D6B-178 withdrawn by D6B-182): [notes.md](notes.md).
Test: `tests/slice6_redacted_failure_test.py`. Fixtures: `slice6/redacted-failure/`, one case per file. Run: [red-output.log](red-output.log).
By: Opus (RED, slice6b-redacted-failure). RED repair changes (O1, O2): By: Opus (RED repair, slice6b-redacted-failure).

## Contract

### Direct value (D6B-67, D6B-174)

- A variable that a record pattern binds to a redacted field, at any pattern depth, also under another name (`Order { card_holder: h }`).
- A call `f(v)` or a pipe step `v |> f` with a direct `v`, when `f` is a BEAML fn with one parameter and every clause body of `f` is that parameter unchanged. One level only.
- A call `f(x)` or a pipe step `x |> f` into a one-parameter BEAML fn whose every clause body is a direct redacted value (an accessor, D6B-182). The copy is checked at the call site; the accessor itself builds. One level only.
- "Every clause": a fn with one qualifying clause only is neither an identity fn nor an accessor (`l6`, `l7`).
- Everything else is derived and not checked: `+`, any other call or pipe step, a constructor, a fn that builds a record from its parameter. A fn parameter is never direct.

### Rejected places (DL-105, DL-112)

- (a) A field value of a record literal, also nested, when that field is not `redacted`.
- (b) A variant payload, also a variant as a pipe step (`v |> Held`).
- (c) The whole clause body when its TYPE is the failure TYPE.

### Texts (exact first two stderr lines; a later `  at byte N` line is allowed, D6B-153)

- Record field, failure TYPE (D6B-67 a):
  `error: fn N copies the redacted field F of T into G of the failure TYPE E, which is not redacted`
  `  help: mark H as redacted in D, or do not copy the value (DL-105)`
- Record field, other TYPE (D6B-175):
  `error: fn N copies the redacted field F of T into G of the TYPE R, which is not redacted`
  `  help: mark H as redacted in D, or do not copy the value (DL-112)`
- Payload or body (D6B-67 b, c; D6B-175, D6B-176):
  `error: fn N copies the redacted field F of T into the failure TYPE E, which cannot hold a redacted value` / `  help: do not copy the value (DL-105)`
  `error: fn N copies the redacted field F of T into the TYPE E, which cannot hold a redacted value` / `  help: do not copy the value (DL-112)`
- N: the fn that holds the copy. F of T: the redacted field and the TYPE that declares it (D6B-177). G: the target field, dotted from the outer literal TYPE. H of D: the target field and the TYPE that declares it. E for (b): the enum of the payload.
- Exit 1, empty stdout.

## Tests

| Test | Cases | Fixtures | Today |
|---|---|---|---|
| `test_F1_failure_record_field_copy_is_rejected` | plan F1 (first RED) | `f1_failure_record` | FAIL (exit 0) |
| `test_failure_type_copies_are_rejected` | plan F3, F4, D6B-67 (c) | `f3_failure_enum`, `f4_failure_nested`, `f7_failure_body` | FAIL (exit 0) |
| `test_DL112_copies_everywhere_are_rejected` | DL-112: plain record field, pipe step into an identity fn, call of an identity fn, enum payload, variant pipe step, renamed binding, nested pattern, call and pipe step into an accessor (D6B-182) | `d1` to `d9` | FAIL (exit 0) |
| `test_allowed_copies_build` | redacted target (DL-112), plan F2, DL-113 same name with another value, plan F6 whole record | `g1` to `g4` | pass (guard) |
| `test_limit_derived_values_are_not_checked` | plan F5 `+`, constructor of another TYPE, fn that builds a record, two identity levels, the accessor alone, first-clause-only accessor, last-clause-only identity | `l1` to `l7` | pass (limit) |
| `test_setup_red_sources_build_without_redacted` | setup control | `f*`, `d*` without `redacted` | pass |
| `test_fmt_keeps_every_fixture` | `fmt` exit 0, bytes unchanged | all | pass |
| `test_fixture_set_is_complete` | each file in one group | all | pass |

## Acceptance (GREEN)

- Every test of `tests/slice6_redacted_failure_test.py` passes with the HEAD compiler build.
- The plan checks pass ("Checks, every sub-step"). Sources without `redacted` give byte-equal output.

## Exclusions and limits

- Derived values and implicit flow (DL-029 target). The limit tests pin today's outcome; a later flow check changes them.
- The accessor itself (`-> String = card_holder`) builds: no redacted return form exists. Its call sites are checked (D6B-182, `l5`, `d8`, `d9`).
- No field access form exists (`o.card_holder` does not parse), so no case for it.
- Compile only. No runtime harness, so no fixture passes a failure struct back as a host value (red-team-01 B4).
- `redacted` in an enum payload stays a D6B-64 reject; a redacted value can never stand in a payload.

### Docs additions (2026-11-07, after TEST PASS of 51fd79b2)

By: Opus (docs slice6b/6c). The lines above stay as the RED record.

- **[Verified]** `o |> holder |> Holder` (an accessor step, then the constructor of a plain `Holder { name: String }`) builds. It is a limit like `l2`: a constructor step makes a derived value (D6B-193). `o |> holder |> Held` (a variant step) is the payload reject.
- **[Verified]** Review O1 (medium): a derived copy reaches the store. An accessor, then a fn that builds a record (`fn wrap s: String -> Lookup = Lookup { name: s }`), then the EFFECT builds. The live run writes the value in plain form to `responses.jsonl` and the span. The D6B-72 stored-value block does not see it later, because the stored field `name` is not redacted. This is inside the DL-112 limit ("only the direct copy is caught", limit `l3`). It is evidence for the flow check (DL-029).
- **[Verified]** Review O2 (medium): the reach covers one-parameter fns only (D6B-174, D6B-182). A two-parameter accessor (`fn pick Order { card_holder }, x: String -> String = card_holder`) and a one-parameter failure builder (`fn bad s: String -> Bad = Bad { reason: s }`) build. An unused second parameter bypasses the accessor rule.
- **[Verified]** D6B-191: `fmt` does not run this check. `fmt` gives exit 0 on a source that the build rejects (`f1_failure_record.beaml`). `fmt` exit 0 is not a validity check; use the build.
