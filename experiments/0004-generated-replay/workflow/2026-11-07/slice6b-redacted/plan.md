# Plan: slice 6b step 6, `redacted`, `with` and the RESPONSE RECORD projection

**[Proposal]** PLAN phase, 2026-11-07. Replan of step 6 of the [slice 6b plan](../slice6b-plan/plan.md#step-6-redacted-and-with-slice6b-redacted) on the OWNER decision DL-105. Task records only. No production file, no commit, no `run.py` run.
Inputs: DL-029, DL-032, DL-033, DL-059, DL-089, DL-102, DL-103, DL-105 in [the decision log](../../../../../wiki/planning/decision-log.md); [slice 6b decisions](../slice6b-plan/decisions.md) D6B-29 to D6B-35; [plan review](../slice6b-plan/plan-review.md) O1 and O2; the step 7 and step 8 ledgers ([decode-literals](../slice6b-decode-literals/notes.md), [decode-constructor](../slice6b-decode-constructor/notes.md)); `experiments/0001-syntax-to-beam/src/main.rs`; the slice 2 to 5 replay tests, `arms_test.py`, `run.py`; the GEN copies of the 0003 tests; the grammar corpus (`integrations/zed-beaml/test/corpus/forms.txt`, `constructors.txt`).
Design decisions that the decision log does not settle: [decisions.md](decisions.md) (D6B-52 to D6B-72, OWNER questions Q6B-10 to Q6B-15). Machine form: [plan.json](plan.json).
By: Opus (PLAN, slice6b-redacted) for every proposal in this file (DL-107). OWNER questions are decided later by `13ue`.
Also read: DL-106 (constructor TYPES become structs at the host, generated `new/1`). It touches 6b at Q6B-15 (was D6B-63) and D6B-71.

## Plan repair

**[Proposal]** PLAN REPAIR, 2026-11-07, on the [plan check](plan-review.md) (BLOCK on O1 and O2). The three sub-steps stay.
By: Opus (PLAN REPAIR, slice6b-redacted) for every item in this section and every changed or new entry below.

- **O1.** `--stored` blocks on a record whose `version` is not `2` (D6B-59 changed). New test 6a P6 with the exact text. Why: a record that the build cannot read must block (DL-031, DL-040).
- **O2.** A field that becomes `redacted` while stored records hold its value blocks for INPUT fields too, by a count of stored values in `request` and `value` (new D6B-72). New test 6b R8. Q6B-11 names the input case. Why: the input TYPE has no fingerprint in the record.
- **O3.** New echo case R4c (same-named plain output field), a file-backed `:otel_span.set_attribute` stub, and a scan for the base64 and hex forms of the MARKER (D6B-70 amended). R4 expects dotted `unknown_keys` names (D6B-56 amended). Why: three channels were not scanned.
- **Raised to Migrate.** D6B-62 is now Q6B-14, D6B-63 is now Q6B-15, two options each. D6B-66 folds into Q6B-11 Part 1. Why: each changes generated behaviour, syntax or stored-record readability (PC6R-2).
- **Q6B-10.** New option C (LIB frozen, compare outcomes and counts only). Q6B-10 now blocks only the GEN copy run and `overlay_diff_test.py`.
- **Q6B-13 (new, Answer).** A redacted input field and a same-named plain output field. Evidence and challenges, no recommendation.
- **Blocks.** 6b RED can start after 6a. 6b GREEN waits for Q6B-11 (R7, R8), Q6B-13 (R4c), Q6B-14 (R5) and Q6B-15 (R6).

## What changes against the old step 6

- **[Verified]** DL-105 supersedes D6B-34 (compile error on a redacted output field) and the D6B-30 and D6B-32 readings.
- **[Verified]** DL-105: the raw body is stored nowhere. This holds for every RESPONSE RECORD, not only for TYPES with a redacted field.
- **[Inference]** So the record change touches every EFFECT and every old replay test. The old risk line "sources without `redacted` give byte-equal output" is false now.
- **[Proposal]** The step splits into three sub-steps. Each has one concern and one RED/GREEN round.
  By: Opus (PLAN, slice6b-redacted).

## Facts the sub-steps build on (observed in `main.rs` at HEAD ee249e5b)

- `Replay.record/3` writes `version: 1`, `request` (the full EFFECT input), `status`, `body_base64`, `body_length`, `body_sha256`, `unknown_keys` (only when the decode passes, else `[]`) and `type`.
- The REPLAY RUN checks `operation`, `attempt`, `request` (`:request_mismatch`), `status`, then `body/1` (`:body_digest_mismatch`), then the decode of the bytes.
- The versioned decode already does `Map.take(body, names)` of the record's TYPE VERSION before the MIGRATE CHANGES. Other keys go to `unknown_keys`. **[Inference]** A projection by the TYPE VERSION at write time gives the same replay result for every valid record.
- `Http.post/4` sends `ProbeSupport.json(request)`: the full input today.
- `ProbeSupport.span/5` reads only `order["order_id"]` from its input argument. `ProbeSupport.event/2` logs names only. **[Verified]** `experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex`.
- The arm replay counts include `":json.decode/1": 1` (`arms_test.py`, `decode_error` and R2).
- No `redacted`, no `with` in the compiler. The grammar has both (`_field_type`, `effect ... with commaList(property)`). The corpus also has `drop secret: redacted String` in a MIGRATE CHANGE.

## Sub-step order

| # | Sub-step | Ledger | Depends on | Blocked by |
|---|---|---|---|---|
| 6a | RESPONSE RECORD = projection for every record. No `redacted` yet. All old tests adapted. | `slice6b-record/` | step 7 GREEN, step 8 GREEN | **Q6B-10** (GEN copy run and `overlay_diff_test.py` only) |
| 6b | `redacted` on fields, `with` on EFFECTS, wire and record projections, marked fields, echo test, stored-value block | `slice6b-redacted/` | 6a | GREEN: **Q6B-11**, **Q6B-13**, **Q6B-14**, **Q6B-15** |
| 6c | Failure TYPE rule: no non-redacted copy of a redacted field (DL-105) | `slice6b-redacted-failure/` | 6b | — |

- **[Proposal]** 6a runs after steps 7 and 8 GREEN (D6B-52). Both RED files hold `body_base64` fixtures. 6a then adapts every record test in one pass, also theirs.
- Step 10 (`fmt`) is independent. A `with` tail on an EFFECT line is not in the step 10 fixtures (exclusion there).

## Contract

### RESPONSE RECORD, version 2 (6a)

| Key | Meaning | Decision |
|---|---|---|
| `version` | `2` | D6B-53 |
| `trace_id`, `client_span_id`, `artifact_id`, `operation`, `attempt`, `status`, `type` | unchanged | — |
| `request` | the EFFECT input without any redacted field (6b). In 6a it is unchanged, because no field is redacted yet. | D6B-32, D6B-61 |
| `value` | the wire values under the declared keys of the newest TYPE VERSION. Not validated. Redacted keys removed. Nested by DL-099 and D6B-49. `null` when the body is not a JSON object. | D6B-54 |
| `redacted` | sorted names of the redacted declared fields that were present and valid at write time. `[]` in 6a. | D6B-55 |
| `unknown_keys` | sorted names of the other keys (dotted for nested keys, step 8 S8). Names only. Now also for a body that fails the decode. | D6B-56 |
| `unknown_fields` | the step 7 key (if step 7 GREEN keeps it). Not part of the digest. | D6B-53 |
| `value_sha256` | lower-case hex SHA-256 of the canonical JSON of `{"redacted", "unknown_keys", "value"}` | D6B-58 |
| `body_base64`, `body_length`, `body_sha256` | removed | DL-105 |

- The same projection applies for every status (D6B-57).
- **[Inference]** The record format change is DL-105 itself (OWNER, Answer). The key names are a Repair (DL-105: "names are a sketch").

### REPLAY RUN (6a)

- The checks keep their order and their six reasons. `body/1` becomes the digest check of the projection. A mismatch stays `:body_digest_mismatch` (D6B-58).
- `--stored`: a record whose `version` is not `2` is a build error (D6B-59). At replay, a record without `value` (version 1, raw body) still gives `:body_digest_mismatch` as a second guard.
- The decode reads `value` through the existing decode path. It re-encodes `value` to bytes, so the arm counts keep `":json.decode/1": 1` (D6B-60).
- The replay span attribute `unknown_keys` is the sorted union of the record `unknown_keys` and the stray keys that the decode finds in `value` (D6B-60).

### `redacted` and `with` (6b)

- Parse `name: redacted TYPE` in a `type` only (D6B-29). Everywhere else a compile error (D6B-64).
- Parse `with f1, f2` after the `)` of the EFFECT target (D6B-31). Each name is a top-level redacted field of the EFFECT input TYPE. Unknown, not redacted, duplicate: compile errors (D6B-65).
- Wire body: the input without every redacted field at any depth, except the `with` names (DL-089, D6B-32).
- Record `request`, the `:request_mismatch` compare, the span input argument and `ProbeSupport.event`: the input without every redacted field, `with` names included (D6B-32). The key is removed; no placeholder (D6B-33).
- EFFECT output: a redacted field is legal (DL-105). Which field TYPES 6b allows is Q6B-15 (was D6B-63, DL-106).
- The redaction helpers work on the plain map form. A struct input (DL-106) goes through `Map.from_struct/1` first (D6B-71).
- The live decode returns the real value to the flow. The record keeps only the name in `redacted`.
- How the REPLAY RUN shows a marked field is Q6B-14 (was D6B-62). A redacted field that is missing or invalid at write time is not marked, so the replay gives the same `decode` reject as live (D6B-55).
- A field that becomes redacted while stored records hold its value blocks the build: `--stored` counts stored values under that field in `request` (input TYPE) and `value` (output TYPE) (D6B-72). Whether `redacted` is part of the fingerprint, and the exit, are Q6B-11 (D6B-66 folded in).
- A redacted input field and a same-named plain output field: Q6B-13 (Answer).

### Failure TYPE rule (6c)

- A compile error when a value that comes directly from a redacted field stands in a failure value of a non-redacted place (DL-105, D6B-67).
- Direct means: a variable bound to a redacted field by a record pattern, used as such. A `+`, a call or a pipe makes a derived value. Derived values are out of scope (DL-105, DL-029 target).
- Non-failure TYPES: not checked in 6c. Q6B-12 (Answer) asks the OWNER.

### Out of scope

- Derived values and implicit flow (`"Hello " + holder`), DL-029 target.
- Dotted `with` paths. A nested redacted input field is never sent (D6B-31).
- `redacted` in enum payloads, signature lines and MIGRATE CHANGES. The corpus line `drop secret: redacted String` is a known grammar/compiler gap.
- `redacted` on an enum, constructor or record field of an EFFECT output TYPE, if Q6B-15 keeps option A.
- The release path of the echo test (real ProbeSupport, Logger handler, OTel exporter). The `run.py` proxy writes raw wire exchanges into its results; it is test tooling, not BEAML output (limit L2).
- A MIGRATE CHANGE for a field that becomes redacted (Q6B-11).
- The LIB arm record format (Q6B-10).

## Old tests that change in 6a (class Repair: our own contract, pre-production, D6B-52)

**[Verified]** by `rg body_base64|body_sha256|body_length|request_mismatch|unknown_keys` outside `results/`.

| File | Place | Assertion today | After 6a |
|---|---|---|---|
| `tests/arms_test.py` | `with_body` (l. 284) | builds `body_base64`, `body_length`, `body_sha256` | replaced by `st.with_value` (D6B-68) |
| `tests/arms_test.py` | L1 (l. 416) | `bytes` == base64 of `UNKNOWN_KEY_BODY`; `record_hint` `["fraud_score"]` | `value` == `PAYMENT`; hint unchanged; `"low"` in no record byte |
| `tests/arms_test.py` | L2 (l. 440) | 503 record `bytes` == base64 of `VALID_BODY` | `value` == `PAYMENT` (D6B-57) |
| `tests/arms_test.py` | L3 (l. 458) | `bytes` == base64 of `MISSING_KEY_BODY` | `value` == `{"order_id": "order-1"}` |
| `tests/arms_test.py` | R1, R3 (l. 491, 503), outcomes R1 (l. 568) | `with_body(..., MISSING_KEY_BODY / WRONG_TYPE_BODY)` | `with_value`; expected `decode_error()` unchanged, `":json.decode/1": 1` stays (D6B-60) |
| `tests/arms_test.py` | R2 (l. 495) | replay hint `[["fraud_score"]]` from the raw body | same hint, from the record `unknown_keys` (D6B-60) |
| `tests/arms_test.py` | `EIGHT_CASES` | from the GEN copies of the 0003 tests | names unchanged; the copies are Q6B-10 |
| `tests/slice2_replay_test.py` | C11, C12, C9/C14 builders (l. 133, 140, 146), l. 204 | `arms.with_body(records(V1)[0], body)` | `st.with_value`; expected values unchanged |
| `tests/slice3_replay_test.py` | `replay` (l. 129-130) | `arms.with_body(record, json bytes)` | `st.with_value(record, dict)`; D11b, D11c keep their meaning by D6B-60 |
| `tests/slice4_retire_test.py` | `with_body`, `make_record` (l. 211-230) | raw body per TYPE VERSION | `value` per TYPE VERSION; `slice4_replay_test.py` uses it unchanged |
| `tests/slice5_syntax_test.py` | `make_record` (l. 269-278), l. 547 | inline `body_base64`, `body_sha256` | `st.with_value`; `slice5_replay_test.py` uses it unchanged |
| `tests/stored_types_test.py` | `v1_record()` (l. 56) | reads `stored/v1.jsonl` | fixture converted (D6B-69); new helper `with_value` lives here |
| `stored/v1.jsonl`, `stored/v1-v2.jsonl` | fixture | version 1, raw body | version 2 projection (D6B-69) |
| `slice6/decode/stored*.jsonl`, `slice6/decode-ctor/stored*.jsonl` | step 7, 8 fixtures | raw body | projection; the DL-102 `--stored` check reads `value` |
| `tests/slice6_decode_test.py`, `tests/slice6_decode_ctor_test.py` | captured record, replay records | `body_base64` in records | `value`; `unknown_fields`, `unknown_keys` assertions unchanged |
| `run.py` | `body_json` (l. 398), `classify_replay` (l. 434) | reads `body_base64` of the old record | reads `value` of a GEN record; proxy exchanges stay raw (test tooling) |
| GEN copies of 0003 `response_capture_test.py` | l. 180-192 | `body_length`, `body_sha256`, `first_response_body` | projection keys; **Q6B-10** |
| GEN copies of 0003 `replay_run_test.py` | l. 227, 262-263, 312-323, the stub record writer | raw body equals `PAYMENT`; `a1_record_bytes_equal_sent_bytes`; `replay_a1_noncanonical_body`; tamper of `body_base64` | projection form; a1 becomes "key order does not matter"; tamper of `value`; **Q6B-10** |
| `tests/overlay_diff_test.py`, `arms/gen/assertion-changes.json`, README table "0003 lines that change" | change table | fixed GEN rows | new GEN rows; **Q6B-10** |

No change: `tests/cli.rs` (no body key), `tests/payments.generated.snapshot` (no `Replay`), the `--stored` TYPE checks (`type` key; 6a adds only the `version` check of D6B-59), the LIB overlay and `arms/lib/freeze.json` under option A of Q6B-10.

Docs in 6a: the glossary row RESPONSE RECORD says "body bytes". The 6a docs phase updates it (projection, not body).

## First failing test per sub-step

### 6a: `tests/slice6_record_test.py`

- Harness: the release-free stubs of step 7 (`slice6_decode_test.STUBS`), source `arms/gen/orders.beaml`, `--stored stored/empty.jsonl`.
- **P1 (first RED).** Call `OrdersBeamlSpike.Replay.record(%{"order_id" => "order-1"}, 200, UNKNOWN_KEY_BODY)`. The captured record has `version: 2`, `value: {"order_id": "order-1", "status": "authorized"}`, `redacted: []`, `unknown_keys: ["fraud_score"]`, `value_sha256` equal to the Python canonical digest, and no key `body_base64`, `body_length`, `body_sha256`. The JSON of the record does not contain `low`. Today: `version: 1` and `body_base64` are present.
- P2: `Replay.run/3` over that record gives `{:ok, PAYMENT}`; a changed `value` with the old digest gives `:body_digest_mismatch`; a version 1 record gives `:body_digest_mismatch`.
- P3: a body that fails the decode (`MISSING_KEY_BODY`) gives `value: {"order_id": "order-1"}` and replays as the typed reject `decode`.
- P4: a body that is not JSON gives `value: null`, `unknown_keys: []`. A 503 body gets the same projection.
- P5: digest parity. Elixir and Python give the same `value_sha256` for one ASCII and one non-ASCII value.
- P6 (O1): `--stored` with one version 1 record of `stored/v1.jsonl` (taken before the conversion) with a correct `type` key. Expect exit 1 and stderr exactly `error: stored RESPONSE RECORD has record version 1; this build reads record version 2 only (DL-105)` and `  record source: S:1 (line 1)`. A record without `version` gives `V` = `none`. Today (inferred): the build passes.
- Then: every old test in the table above passes with only the listed changes.

### 6b: `tests/slice6_redacted_test.py`

- Harness: own stubs. `ProbeSupport.json/1` encodes for real. `ProbeSupport.config(:payments_port)` returns the loopback stub port from an environment variable. `ProbeSupport.span/5` and `event/2` append their arguments to a file in the RUN DIRECTORY. `ProbeSupport.Capture.write/2` appends `ProbeSupport.json(record)` to `responses.jsonl` in the RUN DIRECTORY.
- **R1 (first RED).** `orders.beaml`: `type Order { order_id: String  card_holder: redacted String }`, EFFECT without `with`. The loopback stub receives a body without `card_holder`. Today: the parse fails at `redacted`.
- R2: `orders-with.beaml` (`with card_holder`): the wire body has `card_holder`. The record `request`, the span input and the event file have no `card_holder` key.
- R3: the replay `:request_mismatch` compare uses the projection: a record `request` without `card_holder` replays; a record with it gives `:request_mismatch`.
- R4 (echo, plan review O2): the stub echoes the full request in its response, at the top level and under the key `echo`. Two sources: the output TYPE declares `card_holder: redacted String`; the output TYPE does not declare it. Positive controls: the stub memory holds the MARKER in the request and in the response. Assert: the MARKER is in no file of the RUN DIRECTORY and not in `.beaml/actions.jsonl`. First case: `redacted: ["card_holder"]`, `unknown_keys: ["echo", "echo.card_holder", "echo.order_id"]`. Second case: `redacted: []`, `unknown_keys: ["card_holder", "echo", "echo.card_holder", "echo.order_id"]` (dotted per level, D6B-56).
- R4c (O3): the output TYPE declares a plain `card_holder: String`. The same echo. The expected outcome is set by the Q6B-13 answer. Before the answer, R4c is recorded as an open case, not as a pass.
- The R4 harness stubs `:otel_span.set_attribute`: it appends its arguments to a file in the RUN DIRECTORY. The scan looks for the MARKER in plain text, in base64 at the three byte offsets and in lower-case hex (D6B-70).
- R5: replay of the R4 record gives the marked form of Q6B-14. A record whose `redacted` list lacks the field gives the typed reject `decode`.
- R6: rejects with exact texts (D6B-64, D6B-65; the Q6B-15 text under its option A).
- R7: a RECORD SNAPSHOT of the output TYPE whose `value` holds `card_holder` against a source with `card_holder: redacted String` fails the build with the D6B-72 text (P = `value`). Under Q6B-11 option 1A the fingerprint error may also show.
- R8 (O2): a stored record with `request: {"order_id": "order-1", "card_holder": "x"}` against a source that marks `Order.card_holder` as `redacted`. Expect exit 1 and the D6B-72 text with P = `request` and count 1. The value `x` is in no stderr byte. Today (inferred): the build passes.
- The MARKER is `MARKER-` plus a random hex string per run. It goes to the harness through an environment variable, never through a file (D6B-70).
- A scan self-check: the scan finds the MARKER in a planted file outside the RUN DIRECTORY, in each of the plain, base64 and hex forms.

### 6c: `tests/slice6_redacted_failure_test.py`

- **F1 (first RED).** `fn check Order { card_holder } -> String ! Bad = Bad { reason: card_holder }` with `type Bad { reason: String }`: compile error, exact text of D6B-67. Today (after 6b): it compiles.
- F2: `type Bad { reason: redacted String }` with the same clause compiles.
- F3: a variant payload of a failure enum (`! Why`, `Short(card_holder)`): compile error.
- F4: a nested record literal inside the failure value with a non-redacted field: compile error.
- F5: `Bad { reason: card_holder + "" }` compiles (derived value, out of scope). The test name says that it records a limit, not a wanted outcome.
- F6: the whole `Order` value in a failure field of TYPE `Order` compiles (the TYPE keeps the mark).

## Fixtures

- 6a: none new. Conversion of `stored/v1.jsonl`, `stored/v1-v2.jsonl`, `slice6/decode/stored*.jsonl`, `slice6/decode-ctor/stored*.jsonl` by a one-off script kept in the 6a ledger (D6B-69).
- 6b: `slice6/redacted/orders.beaml`, `orders-with.beaml`, `orders-echo-declared.beaml`, `orders-echo-undeclared.beaml`, `orders-echo-plain.beaml` (R4c), `bad/*.beaml` (one reject per file), `stored-unredacted.jsonl` (R7), `stored-request-unredacted.jsonl` (R8). Records for R3 and R5 are built in the test with `st.with_value`.
- 6c: `slice6/redacted-failure/*.beaml`, one case per file.

## Checks, every sub-step

- `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` (0001).
- The six compile-level test files, the slice 6 test files, the sub-step test file.
- `python3 -B experiments/0004-generated-replay/run.py` once at the TEST phase (6a must show the adapted arm and replay tests green).
- `payments.generated.snapshot` byte-equal. Every existing reject keeps its message.
- 6b and 6c: sources without `redacted` and `with` give byte-equal output against the 6a output.

## Limits

- L1 **[Inference]** The release-free harness does not run the real ProbeSupport, Logger handler or OTel exporter. The real `span/5` reads only `order_id`; a source that marks `order_id` as redacted gets `nil` there. Smallest next test: one GEN tree with `orders-with.beaml` under `run.py`, scan of the release RUN DIRECTORY without the proxy file.
- L2 **[Verified]** `run.py` `proxy` writes raw wire exchanges (`request`, `body_base64`) into `results/`. A redacted fixture under `run.py` would put the MARKER there. That is host test tooling, not BEAML output; the scan in L1 must exclude it by name.
- L3 **[Inference]** A REPLAY RUN whose later pure step computes with a marked field (`+`) may raise. This is the derived-value case (DL-105, later).
- L4 **[Unknown]** Whether OTP `:json.encode` and Python `json.dumps(ensure_ascii=False)` agree on every escape. P5 checks one non-ASCII value only.
