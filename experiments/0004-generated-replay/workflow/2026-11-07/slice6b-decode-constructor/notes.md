# Slice 6b step 8: notes

## Solve

What this phase takes from the plan (step 8, D6B-48 to D6B-50), DL-065, DL-084, DL-085, DL-099 to DL-103, the step 3 and step 4 GREEN sections (`new_T_k`, `pick`, signature KEYS) and the step 7 ledger ([../slice6b-decode-literals/](../slice6b-decode-literals/)):

- Baseline: commit `cd379ff0`. The compiler was built from a `git archive` of that commit in a scratch directory, because another worker runs the full suite on the live tree. The test runs with `BEAML_SPIKE` set to that binary.
- **[Observed]** Today `effects()` rejects a constructor TYPE in an EFFECT output field with the D6B-19 text. With a non-empty `--stored` file the first error is `slice 1 decodes String fields only, not Payment.state`. Both are missing behavior.
- **[Observed]** The baseline emits `new_PaymentState_1(a0, a1)`, `new_PaymentState_2(a0)` and `new_Amount_1(a0, a1)`. Direct calls give the expected values of this test (S13).
- **[Observed]** In a module with an EFFECT, the baseline emits `defmodule NoCurrency` after its first use in `__beaml_new_Amount_1`. `elixirc` then fails: `BeamlSpike.NoCurrency.__struct__/1 is undefined`. A pure module emits it first and compiles. GREEN must fix the order, else every runtime case fails.
- **[Observed]** Step 7 is RED, not GREEN. This step uses its proposed forms: the record key `unknown_fields` (S4 there), the DL-102 block lines (S5 there), the reason `decode`.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| S1 | Undo | Test file `tests/slice6_decode_ctor_test.py`, fixture dir `slice6/decode-ctor/`, as the task names them. | Plan name `slice6_decode_constructor_test.py` | The task text is newer than the plan. Only names change. |
| S2 | Undo | One fixture: `Payment { order_id state: PaymentState amount: Amount }`. `PaymentState` has signature 1 (`status`, `decline_reason`) and signature 2 (`code`). `Amount` is a record constructor with two String parameters and the failure `NoCurrency`. | One fixture per constructor kind | One snapshot set, one build, all cases. The corpus clauses (constructors.txt lines 6 to 9) are signature 1. |
| S3 | Repair | **Chose:** lift D6B-19 for a constructor TYPE in an EFFECT output field, also nested (the `Declined(DeclineReason)` payload). Keep D6B-19 for the output TYPE itself, the input TYPE and a failure TYPE. **Over:** lift it in every position. **Because:** DL-101 names the decode; the flat body form of DL-099 (a constructor on the output TYPE) needs its own key rule; the input is an encode. **Commits us to:** an open point P2. | Lift everywhere | Smallest step that the task cases need. |
| S4 | Undo | Decode signatures use String parameters only. | Int parameters | EFFECT outputs decode String fields only today. Point P5. |
| S5 | Repair | **Chose:** when an enum constructor gives its keep-value variant, the decode names the field in `unknown_fields` (span attribute and record key), as step 7 does for literals. **Over:** no flag for constructors. **Because:** DL-103 needs to know that a value was kept; one rule for both decode paths. **Commits us to:** the step 7 open point P2 (record key, Migrate) covers this step too. | No flag | D6B-37, DL-103. |
| S6 | Migrate (open, P1) | **Proposal:** a record constructor failure in a decode is the typed reject with reason `constructor`. | (a) `decode`. (b) The failure TYPE name (`NoCurrency`). | A host can tell a shape fault from a rule fault. No value in the text. (b) changes when a failure TYPE is renamed. DL-101 leaves the name open with the OWNER, and host code matches on the reason, so it is above Repair. |
| S7 | Undo | A missing key or a wrong TYPE for a record constructor parameter is the reject `decode`; the constructor does not run. | Reason `constructor` | It is a shape fault, as D6B-48 for an enum. |
| S8 | Repair | **Chose:** a stray key inside a field value is reported as `FIELD.KEY` (`state.extra`) in the span attribute and the record key `unknown_keys`. **Over:** the bare key (`extra`) or a nested list. **Because:** a bare key is ambiguous with a top-level key; the record key is stored data. **Commits us to:** a dotted name per level for later nesting. | Bare key | D6B-49 says what is declared, not how a stray key is named. |
| S9 | Undo (text, P3) | DL-102 block texts. Record constructor: `error: TYPE T: N stored RESPONSE RECORD(S) of operation OP fail the constructor of C for field F with E` (E is the failure TYPE, the reason of DL-102). Enum constructor: `... match(es) no signature of C for field F`. Then the step 7 lines `  record source: PATH:L (line L)` and the MIGRATE STEP help. One message per TYPE, operation, field and reason. | Text without the reason | DL-102 asks for counts and reasons. A TYPE name is no value. |
| S10 | Undo (text, P3) | D6B-50 text: `error: effect OP: the last clause of signature K of constructor C (field T.F) keeps no String input in the keep-value variant V (DL-065, D6B-50)`, then `  help: bind every input in the last clause and put one String input into V, for example fn C other, _ -> C = V(other)`. K counts signatures in source order. | Text without K | A constructor has several signatures. |
| S11 | Undo | `stored.jsonl` holds a record kept as `Unknown("refunded")` that is still Unknown today. The build has no `note:` line. | A DL-103 case | DL-103 for constructors is not in the task. Point P8. |
| S12 | Undo | The test imports the step 7 stubs, `build` and `assert_rejected` from `slice6_decode_test.py`. | Copy them | One harness. If step 7 GREEN changes these names, this file needs the same change. |
| S13 | Undo | Fixture check before RED: (a) a pure copy of the fixture (no EFFECT) compiles on the baseline; direct calls of `new_PaymentState_1`, `new_PaymentState_2` and `new_Amount_1` give the 6 expected values. (b) A String-field copy without the `Amount` clauses runs the harness: 5 of 5 checks PASS. (c) The fingerprint method reproduces the step 7 hash. | No check | A fixture or harness fault would give a false RED. The copies stay in the scratch directory. |
| S14 | Undo | The D6B-49 case puts the key `code` (a parameter of signature 2) and `extra` in the signature 1 object. Only `state.extra` is reported. | `extra` only | It tests "every parameter name of every signature". |
| S15 | Undo | The D6B-50 reject source runs with `--stored stored/empty.jsonl`. | No `--stored` | As step 7 S10. |

### Points the plan and the decision log do not settle

- **P1 [Open, OWNER, Migrate]** S6: the reject reason `constructor`. The test `amount_constructor_failure_is_typed_reject` depends on it.
- **P2 [Open, Repair]** S3: a constructor on the EFFECT output TYPE itself (the flat body of DL-099), on the input TYPE and on a failure TYPE. D6B-19 stays there in this step. No test asserts it.
- **P3 [Open, Undo]** The texts S9 and S10.
- **P4 [Unknown, Repair]** A record constructor with one parameter: DL-099 says "a one-parameter constructor reads the field's value directly". **[Inference]** This holds for records too, but DL-099 asks about enum constructors. The fixture uses two parameters. Not tested.
- **P5 [Open, Repair]** A decode signature with an Int parameter, and D6B-50 for a signature with no String input (no value can be kept). Not tested.
- **P6 [Inference, Repair]** D6B-49 against DL-099: the parameter name of a one-parameter signature (`code`) is never a key, but it counts as declared. A stray key `code` is not reported.
- **P7 [Inference, OWNER, Migrate]** Step 7 P4 holds here too: `Payment` has an enum field, so D6B-39 forbids a MIGRATE CHAIN, and the DL-102 help line asks for a step that 6b cannot compile.
- **P8 [Unknown, Undo]** DL-103 for a constructor clause that maps a kept value now. Not tested.
- **P9 [Unknown, Repair]** An enum constructor clause whose body can fail (`!`). Not in the fixture.
- **P10 [Open, Migrate]** This step depends on the step 7 open point P2 (the record key `unknown_fields`).

## RED

Command (repository root): `BEAML_SPIKE=<scratch>/basecd37/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_decode_ctor_test.py`. Full output: [red-output.log](red-output.log).
Baseline compiler: commit `cd379ff0`, `cargo build --offline` of a `git archive` copy. Toolchain: cargo 1.94.0, rustc 1.94.0, Elixir 1.18.1 (OTP 27), Python 3.13.12.
Inputs (sha256): `slice6/decode-ctor/orders.beaml` `0ab3223280a5b4cbb1809ecc890634d22fcb846abfab3927e6bcfe4b5e70f09a`; `stored.jsonl` `54d55c6fa21ba71eb9443d04f370d3d1aab80316de311f76a2cca889083eb3cf`; `stored-fail.jsonl` `f2df30ff74f0b03d1bd529e99b8587897aa92fc2d32fddb4aeb6b6131394643f`; `stored-nomatch.jsonl` `81db9ba7dd179d144dff1361886e952e9e5841b188b06c665f409c6b5f7fedfc`; `tests/slice6_decode_ctor_test.py` `bcc1aa84ee53a979d5360e4c055175d30ad22a7cdc38da32768aee2182fe2b61`.
Result: 6 tests, 6 FAIL. Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_stored_records_pass_the_constructors` | exit 0, empty stderr | `effect payments.authorize: slice 1 decodes String fields only, not Payment.state` | No constructor decode. |
| `test_runtime_live_decode` | 13 subtests PASS | stops at build, same text | Same. |
| `test_runtime_replay` | 2 subtests PASS | stops at build, same text | Same. |
| `test_stored_record_fails_the_record_constructor` | S9 text | D6B-19 text | No DL-102 check over constructors. |
| `test_stored_record_matches_no_signature` | S9 text | D6B-19 text | Same. |
| `test_last_clause_does_not_keep_the_value` | S10 text | D6B-19 text | No D6B-50 check. |

### RED checks

- Every failure is a missing behavior. The compiler builds, every case reaches the compiler, every message is a compiler message.
- Each reject asserts the full message. Today's text gives no false pass.
- The action event check runs on every compile (no source text, no path).
- `main.rs` was not changed. `run.py` was not run. No result directory and no other step file was touched. No commit.

## Limits

- The runtime harness uses stubs, not a release (step 7 S8). The TEST phase `run.py` covers the release path.
- The texts (P3), the reason (P1) and the stray key name (S8) are proposals.
- The snapshots are hand-built; no compiler wrote them.
