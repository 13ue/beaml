# Slice 6b step 7: notes

## Solve

What this phase takes from the plan (step 7, D6B-35 to D6B-40), DL-043, DL-054, DL-062, DL-065, DL-082, DL-099, DL-102, DL-103 and the step 4 ledger ([../slice6b-enum/notes.md](../slice6b-enum/notes.md)):

- Baseline: commit `f74be40c`. The compiler was built from a `git archive` of that commit in a scratch directory, because another worker runs the full suite on the live tree. The test runs with `BEAML_SPIKE` set to that binary.
- **[Observed]** Today `effects()` accepts only `String` output fields: `effect payments.authorize: slice 1 decodes String fields only, not Payment.state`.
- **[Observed]** Today the `--stored` check reads only the `type` key of each record. It does not decode `body_base64`.
- **[Observed]** Today `__beaml_decode_<type>/1` is a public `def` and returns `{:ok, shape, unknown_keys}` or `:error`. `Replay.run/3` takes the input, a trace id and the record list.
- **[Observed]** Step 4 GREEN keeps the literals in `Program.literals` and finds the keep-value variant by its shape (D6B-21).
- **[Inference]** Under D6B-36 every String has a variant (a literal or the keep-value variant). So a stored String value can never fail the literal mapping. The DL-102 block for ENUM LITERALS can only come from a value that is not a String.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| S1 | Undo | Test file `tests/slice6_decode_test.py`, fixture dir `slice6/decode/`, as the task names them. | Plan names `slice6_decode_literals_test.py` and `slice6/decode-literals/` | The task text is newer than the plan. Only names change. |
| S2 | Repair | **Chose:** keep D6B-36. An output enum without a keep-value variant is a compile error. **Over:** allow it and let unknown values be the typed reject `decode`. **Because:** D6B-36 comes from DL-065 (OWNER, Migrate); a worker cannot lower it. **Commits us to:** the DL-102 block case for literals is a non-String value. | Drop D6B-36 | The task text "else the typed reject decode" reads as if D6B-36 is not in force. See open point P1. |
| S3 | Undo | The DL-102 block case is a stored value that is not a String (`7`, `8`). | A String with no literal | Under S2 a String always has a variant. |
| S4 | Migrate (open, P2) | **Proposal:** the RESPONSE RECORD gets the key `unknown_fields` (sorted top-level field names with a kept value, no values; `[]` else). A record without the key counts as `[]`. The record `version` stays 1. | (a) No new key: then DL-103 cannot be counted. (b) The `type` key holds the literals of each enum field. | DL-103 needs to know that a value was kept at write time. The record holds no decoded value (D6B-37). (a) makes the DL-103 test impossible. (b) is larger and also finds known-to-known moves, which DL-103 leaves open. This revises D6B-37 "Over: a new RESPONSE RECORD key". |
| S5 | Undo (text, P3) | DL-102 block text: `error: TYPE T: N stored RESPONSE RECORD(S) of operation OP have no variant of E for field F`, then `  record source: PATH:L (line L)` (first failing line), then `  help: declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of T (DL-102)`. One message per TYPE, operation and field. | A text without the field | The field tells where to look. The `record source` line is the form of the existing `--stored` errors. No value in the text. |
| S6 | Undo (text, P3) | DL-103 report: one stderr line `note: TYPE T: N stored RESPONSE RECORD(S) of operation OP kept a value of field F that a literal of E maps now (DL-103)`. Exit 0. No line when N is 0. | A `warning:` line; an event count only | Not a fault, so not `warning:`. stderr keeps stdout the Elixir source. |
| S7 | Undo (text) | D6B-36 text: `error: effect OP: the enum E of T.F has no keep-value variant (DL-065)` and `  help: add the variant Unknown(String) to enum E`. D6B-39 text: `error: effect OP: the enum field T.F cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)` and `  help: remove the MIGRATE CHAIN and the VERSION MARK of T, or make F a String field`. | Texts without the decision ID | The plan gives only the help idea. Other 6b texts name their decision. |
| S8 | Undo | Release-free runtime harness: the generated module compiles with `elixirc --warnings-as-errors` beside stubs of ProbeSupport, `ProbeSupport.Capture`, `OpenTelemetry.Tracer`, `OpenTelemetry.Span`, `:otel_span` and `:otel_propagator_text_map`. The stubs put attributes and the captured record into the process dictionary. | The arms harness with releases (slice 2 to 5 replay tests) | The task asks for a replay case only if it is cheap. `Replay.run/3` with the records of a snapshot file is cheap and runs the same generated replay code. |
| S9 | Undo | Live decode through `__beaml_attempt__(fn -> __beaml_result_payments_authorize(body) end)`. | `__beaml_decode_payment/1` | The result function gives the typed reject and sets the span attribute. Its name is today's name. |
| S10 | Undo | The reject sources run with `--stored stored/empty.jsonl`. | No `--stored` | The test then does not depend on the order of the source check and the "stored TYPE VERSIONS unknown" check. |
| S11 | Undo | Build assertion: only the plan line `defp __beaml_literal_PaymentState(<<"ok">>), do: {<<"PaymentState">>, <<"Authorized">>, []}` (byte form). | All plan lines | The runtime checks test the other clauses. Fewer lines bind GREEN less. |
| S12 | Undo | No byte guards (payments snapshot, `bad/*.beaml`) in this file. | Copy the step 5 guards | The other step files and `run.py` keep them. |
| S13 | Undo | Stored records use the D6B-38 fingerprint: fields `[["order_id","String"],["state","PaymentState"]]`. | Literals in the fingerprint | D6B-38 fingerprint part is not superseded. |
| S14 | Undo | A JSON `null` is a test case of the typed reject (`:null` in Elixir; `nil` encodes as the String `"nil"`). | Only `7` | `null` is the other common non-String. |
| S15 | Undo | Fixture check before RED: copies of `orders.beaml` and of the three inline sources with `state: String` compile on the baseline (exit 0). The runtime helpers ran against the String copy: 6 of 6 checks true. | No check | A fixture or harness fault would give a false RED. The copies are in the scratch directory only. |

### Points the plan and the decision log do not settle

- **P1 [Open, OWNER, Migrate]** The task text implies an output enum without a keep-value variant is legal ("else the typed reject decode"). D6B-36 and DL-065 forbid it. This phase keeps D6B-36 (S2). If the OWNER drops D6B-36 for literal enums, the block test also needs a String case (an enum whose literal was removed).
- **P2 [Open, OWNER, Migrate]** S4: a new RESPONSE RECORD key `unknown_fields`. It changes stored data, so it is above Repair. The tests `record_keeps_unknown_fields`, `record_literal_has_no_unknown_fields` and `test_resolved_unknown_reports_the_count` depend on it.
- **P3 [Open, Undo]** The exact texts S5, S6, S7 and the reject reason name `decode` for a non-String value (D6B-35 says `decode`; no own reason). The format of a report over several TYPES or fields (one message each, sorted by TYPE then field) is not tested.
- **P4 [Inference, OWNER, Migrate]** Under D6B-39 a TYPE with an enum output field cannot get a MIGRATE CHAIN in 6b. So the DL-102 help line asks for a step that 6b cannot compile. A blocked build has no exit in 6b except a change of the store. This is a consequence of D6B-39 plus DL-102, not a test fault.
- **[Unknown, Undo]** A missing enum key in a stored body: a block (like a non-String) or not part of this check. Not tested.
- **[Unknown, Undo]** A compile event count for the DL-103 report (`resolved`). Not tested.
- **[Unknown, Undo]** D6B-40 (enum field in an EFFECT input) has no test in this step. The plan lists it as an exclusion of step 7.
- **[Unknown, Undo]** Several environments (DL-102, DL-103 say "per environment"). One `--stored` file is one environment here.

## RED

Command (repository root): `BEAML_SPIKE=<scratch>/basef74b/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_decode_test.py`. Full output: [red-output.log](red-output.log).
Baseline compiler: commit `f74be40c`, `cargo build --offline` of a `git archive` copy. Toolchain: cargo 1.94.0, rustc 1.94.0, Elixir 1.18.1 (OTP 27), Python 3.13.12.
Inputs (sha256): `slice6/decode/orders.beaml` `05f2b9702e50df5b4c0e45bdcbf8759d3bc145a39b822dff9c8e86de74ac20cf`; `stored.jsonl` `c82a68236b9370e31413b94fd57c643bcdc0abb136a44a9488e6781b1943912a`; `stored-resolved.jsonl` `8f6d5ed83eae7c849e33270ea46feaeef6d7df68d9561d42ca8323a27531f4b9`; `stored-fail.jsonl` `b6d9d64d7f2d69f6bd602084b24897ffe122f3a7419fa6d8d054656353678507`; `tests/slice6_decode_test.py` `cc97daf8bf96d6db41f72cb6552ef9fcbceef6a5cdc253698a5cf28a770d24fd`.
Result: 8 tests, 8 FAIL. Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_stored_values_all_resolve` | exit 0, no stderr, literal line | `effect payments.authorize: slice 1 decodes String fields only, not Payment.state` | No enum output field. |
| `test_resolved_unknown_reports_the_count` | exit 0, S6 note | same text | Same; no DL-103 report. |
| `test_runtime_live_decode` | 8 subtests PASS | stops at build, same text | Same. |
| `test_runtime_replay` | 4 subtests PASS | stops at build, same text | Same. |
| `test_stored_value_without_a_variant_blocks` | S5 text | same text | No enum field, no DL-102 check. |
| `test_output_enum_without_keep_value_variant` | D6B-36 text | same text | No D6B-36 check. |
| `test_enum_output_field_with_a_chain` | D6B-39 text | same text | No D6B-39 check. |
| `test_enum_output_field_with_a_version_mark` | D6B-39 text | same text | Same. |

### RED checks

- Every failure is a missing behavior. The compiler builds, every case reaches the compiler, every message is a compiler message.
- A first run had a setup fault: the inline sources had no `fn` (`expected at least one function`). Fixed (one `fn place` line), then validated (S15). That run is not RED.
- Each reject asserts the full message. Today's text gives no false pass.
- The action event check runs on every compile (no source text, no path).
- `main.rs` was not changed. `run.py` was not run. No result directory and no other step file was touched. No commit.

## Limits

- The runtime harness uses stubs, not a release. A fault in the real ProbeSupport path is not seen here; the TEST phase `run.py` covers the release path.
- The exact texts (P3) and the record key (P2) are proposals. GREEN or the OWNER can change them; then the test changes too.

## GREEN

Commands and results: [green-output.log](green-output.log). Changed files: `experiments/0001-syntax-to-beam/src/main.rs` and `tests/slice6_decode_test.py` (two new tests for the RED review notes N2 and N3, added before the `main.rs` change). The fixtures are not changed (hashes equal to RED). `run.py` was not run. No commit.

### Tests first (RED of N2, N3)

- `test_wire_value_stays_in_the_typed_field` (N3): after a live decode of `"refunded"`, no span attribute and no RESPONSE RECORD key except `body_base64` holds the value, and `.beaml/actions.jsonl` does not hold it.
- `test_written_record_reports_the_count` (N2): a build without `Pending` writes the record of a `"pending"` response through `:json.encode` (the encode of the real `ProbeSupport.json`). The build of `orders.beaml` reads that line with `--stored` and gives the DL-103 note with count 1.
- RED on the HEAD compiler (3687bb4e, `main.rs` unchanged): 2 of 2 FAIL, `slice 1 decodes String fields only`.

### Result (observed)

| Command | Result |
|---|---|
| `slice6_decode_test.py` | 10 tests, 10 OK (8 of RED plus N2, N3) |
| `slice6_int_test.py`, `slice6_failure_test.py`, `slice6_enum_test.py`, `slice6_pipe_test.py` | 16, 22, 20, 12 OK |
| `slice6_constructor_test.py` | 25 tests, 1 FAIL (`test_constructor_type_in_an_effect_output_field`). The same FAIL with the HEAD compiler: commit 3687bb4e changed this test to the step 8 text. Not this step. |
| `slice6_decode_ctor_test.py`, `slice6_struct_order_test.py` | 7 of 7 and 1 of 2 FAIL, the same with the HEAD compiler (RED of other steps) |
| `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` | pass |
| `cargo test --offline --no-fail-fast` | 31 pass (17 unit, 14 CLI) |
| `stored_types_test.py`, `slice3_types_test.py`, `slice4_retire_test.py` | 33, 69, 87 OK |
| `slice5_syntax_test.py`, `slice5_squash_test.py`, `slice5_rewrite_test.py` | 60, 24, 5 OK |
| Byte-equal, HEAD compiler against GREEN | `payments.beaml` and `arms/gen/orders.beaml` byte-equal; every other `slice6/**/*.beaml` equal, except `slice6/decode/orders.beaml` (exit 1 to 0) |

### Decisions

- **G1 · Undo.** The check order per output field: a literal enum in a TYPE with a MIGRATE CHAIN or a VERSION MARK gives D6B-39 first, then a literal enum without a keep-value variant gives D6B-36. An enum without literals keeps the text `slice 1 decodes String fields only` (step 8 changes it). Alternative: D6B-36 first. Reason: the D6B-39 sources have a keep-value variant, so the order is not visible in a test; a versioned TYPE has no literal decode at all.
  By: Opus (GREEN, slice6b-decode-literals)
- **G2 · Undo.** The keep-value variant is found by its shape: the one variant `X(String)` without a literal (`keep_variant`, D6B-21). Alternative: a fixed name `Unknown`. Reason: step 4 finds it by shape too.
  By: Opus (GREEN, slice6b-decode-literals)
- **G3 · Repair.** **Chose:** `__beaml_literal_E` is emitted only for an enum that is a field TYPE of an EFFECT output, with the plan shape (one clause per literal, then `when is_binary(v)` to the keep-value variant, then `:error`). The decode applies it to the field after `Map.take` and before `__beaml_valid__`. **Over:** emit it for every literal enum. **Because:** the step 4 test asserts that a literal enum without an EFFECT emits no `__beaml_literal_` function, and String-only outputs keep their bytes. **Commits us to:** a missing key stays missing and fails `__beaml_valid__` (the typed reject `decode`). **[Inference]** An invalid UTF-8 String goes to the keep-value variant and then fails `__beaml_valid__` (typed reject); not tested.
  By: Opus (GREEN, slice6b-decode-literals)
- **G4 · Repair.** **Chose:** the decode keeps its return shape `{:ok, shape, unknown_keys}`. A public helper `__beaml_unknown_fields_<type>(value)` gives the sorted field names whose value is the keep-value variant. The result function sets the span attribute `unknown_fields` only when the list is not empty. **Over:** a 4-tuple from the decode. **Because:** the decode and its callers stay unchanged; the record writer and the result function read the same helper. **Commits us to:** the helper reads the typed value, so it stays correct when DL-105 makes the RESPONSE RECORD a typed projection.
  By: Opus (GREEN, slice6b-decode-literals)
- **G5 · Repair.** **Chose:** the RESPONSE RECORD key `unknown_fields` (names only, the S4 proposal) is written only when the output TYPE has a literal enum field. A record without the key counts as `[]`. **Over:** the key in every record. **Because:** `payments.beaml` and the orders output must stay byte-equal, and the other step files read String-only snapshots. **Commits us to:** P2 stays open for the OWNER; DL-105 (step 6) can keep the key as a names-only list beside `unknown_keys`.
  By: Opus (GREEN, slice6b-decode-literals)
- **G6 · Repair.** **Chose:** the `--stored` check decodes `body_base64` (own base64 decoder, no new dependency) and maps each literal enum field of a record whose `type` name is the output TYPE. A value that is not a String (a number, `null`, a missing key, or a body that is not JSON) counts as a failure. A String that is a literal, in a record whose `unknown_fields` names the field, counts as resolved (DL-103). Path errors (no TYPE VERSION path) come first; the DL-102 block runs only when there are none. **Over:** a missing key as no failure. **Because:** the live decode rejects a missing key too, so it is the same mapping failure. **Commits us to:** a record with a broken body gives the DL-102 text, not a body text. The open Undo point "missing enum key" is closed by this choice and is not tested.
  By: Opus (GREEN, slice6b-decode-literals)
- **G7 · Undo.** DL-102 text for one record: `1 stored RESPONSE RECORD ... has no variant`; for more: `RECORDS ... have`. DL-103 note: `RECORD` or `RECORDS`, `kept` for both. One message per TYPE, operation and field, sorted. Alternative: always `have`. Reason: English grammar; only the plural is tested.
  By: Opus (GREEN, slice6b-decode-literals)
- **G8 · Undo.** The `note:` lines go to stderr after the Elixir source and before the DEAD LINE warnings, through a new `Build.notes` field. The unit test seam `still_dead` gets `notes: Vec::new()` (a struct field, no behavior change). Alternative: a thread-local like `LAST_TYPES`. Reason: smaller and explicit.
  By: Opus (GREEN, slice6b-decode-literals)
- **G9 · Undo.** No action event count for the DL-103 note. Alternative: a `resolved` count. Reason: not tested (open Undo point); the event code is unchanged and records no value.
  By: Opus (GREEN, slice6b-decode-literals)

### Deviations

- The task names 10 checks; the file has 10 tests (8 of RED plus N2, N3). All pass.
- The constructor test is not 25 of 25: one assertion differs because commit 3687bb4e (step 8 RED repair, another worker) changed it. The HEAD compiler fails it in the same way.
- Step 6 (DL-105, typed projection) is not implemented here, as the task says.

### Limits

- **[Observed]** The N2 case uses `:json.encode`, as the real `ProbeSupport.json` does, but the Capture GenServer and the release path are stubs. `run.py` (TEST phase) covers the release path.
- **[Inference]** The RED review note N1 (a removed literal turns a known value into Unknown, with no block and no count) is not changed by this GREEN. It stays an OWNER question.
- **[Inference]** P4 stays: the DL-102 help line asks for a MIGRATE STEP that D6B-39 rejects in 6b.
