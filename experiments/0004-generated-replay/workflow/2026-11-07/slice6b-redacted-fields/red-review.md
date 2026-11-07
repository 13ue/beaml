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
