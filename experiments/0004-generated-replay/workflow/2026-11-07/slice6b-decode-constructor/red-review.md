# Slice 6b step 8: RED review

Fresh-context RED REVIEW, 2026-11-07. Not a Devil's Advocate round. Target: [spec.md](spec.md), [notes.md](notes.md), [red-output.log](red-output.log), `tests/slice6_decode_ctor_test.py`, `slice6/decode-ctor/`. Baseline: commit `cd379ff0`, own `git archive` copy, `cargo build --offline`. The live tree was not built. `run.py` was not run. No production file and no test was changed.

## Verdict

**BLOCK.** Objection 1 is critical. Objection 2 is high.

## Rerun

**[Observed]** `BEAML_SPIKE=<scratch>/rr8/.../beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_decode_ctor_test.py`: 6 tests, 6 FAIL, the same messages as `red-output.log`. `main.rs` has no change between `cd379ff0` and `HEAD`.

## Objections

### 1. Critical: three tests compile the step 7 fixture, not the step 8 fixture

- **[Observed]** The test sets `build = sd.Slice6Decode.build`. That function reads the global `ORDERS` of `slice6_decode_test.py`. `sd.Slice6Decode.build.__globals__["ORDERS"]` is `slice6/decode/orders.beaml` (step 7, ENUM LITERALS, `Payment { order_id state }`).
- **[Observed]** Thus `test_stored_records_pass_the_constructors`, `test_runtime_live_decode` and `test_runtime_replay` compile the step 7 fixture with the step 8 `stored.jsonl`. The step 7 fixture with that file gives `slice 1 decodes String fields only, not Payment.state`. The step 8 fixture with that file gives the D6B-19 text. This is the cause of the two RED messages. The notes explanation ("with a non-empty `--stored` file the first error is ...") is wrong.
- **Wrong outcome:** after a correct GREEN, these 3 tests still fail. The step 8 snapshots carry the fingerprint of the 3-field `Payment`, and the step 7 runtime has no `amount` field and no constructor decode. The RED is false for half the step, and a GREEN worker is pushed to bend the compiler or the test.
- **Smallest fix:** a local `build` in the step 8 test that compiles the step 8 `ORDERS` (the same 4 lines as step 7). Then rerun RED and record the new messages. Correct the [Observed] line in notes.md.

### 2. High: the struct order fault is a step 2 defect. Fix it and test it before step 8 GREEN

- **[Observed]** `emit()` puts the failure structs first only when the module has no EFFECT (D6B-07). With an EFFECT, `emit_effect` puts them after the clauses.
- **[Observed]** Probe without any step 8 feature, on the baseline: compile exit 0, then `elixirc` fails (`cannot compile module BeamlSpike`), because `%__MODULE__.Bad{}` comes before `defmodule Bad`:

```
type Order { order_id: String }
type Bad {}
fn check "" -> String ! Bad = Bad {}
fn check x: String -> String ! Bad = x
type Payment { order_id: String }
type PaymentError { reason: String }
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")
fn place order: Order -> Payment ! PaymentError = order |> payments.authorize
```

- **[Observed]** Origin: commit `c3e97430` (step 2 GREEN) added the order rule. A scan of every `.beaml` file with an EFFECT under `experiments/0004-generated-replay/` (about 45 files): no file that compiles uses a failure struct before its `defmodule`. The existing EFFECT fixtures are not affected. **[Inference]** No step 2 to step 5 runtime test compiles an EFFECT module with a pure fallible clause, so the fault stayed hidden.
- **Wrong outcome:** if step 8 GREEN fixes it, the fix has no test of its own. The step 8 runtime tests cover it only through `Amount`. The D6B-07 byte-identity of the orders output can break without a named test.
- **Smallest test:** the probe above as a step 2 regression case: build, `elixirc --warnings-as-errors` exit 0, and the orders output stays byte-identical (D6B-07). Fix it as a separate Repair before step 8 GREEN.

### 3. Medium: DL-085 (first match) is not proven between signatures

- **[Observed]** Signature 1 needs an object. Signature 2 reads a scalar (DL-099 B). No field value matches both. A GREEN that tries the signatures bottom to top, or "most keys first", passes all 6 tests.
- **[Observed]** Only the clause order inside signature 1 is tested (`"ok", _` before `other, _`). That is the order of the Elixir clauses.
- **Wrong outcome:** a value that matches two object signatures decodes through the wrong one, silently.
- **Smallest test:** one inline source with two object signatures that share a key, for example `(status, decline_reason)` and `(status, code)`, and one value with all three keys. Expect the variant of the first signature.

## Checks of the main-agent classes

- **P1, reason `constructor` (Repair):** encoded exactly once, in `amount_constructor_failure_is_typed_reject`. A missing key stays `decode` (S7). The `--stored` block names the failure TYPE `NoCurrency`; that is the DL-102 reason text (S9), not the reject reason. Nothing wider. **Record gap:** notes.md S6 and P1 still say "Migrate (open)". Record the new class and who changed it.
- **S3, lift D6B-19 for output FIELDS only (Repair):** the step 8 test does not assert that D6B-19 stays. **[Observed]** The step 3 tests do: `test_constructor_type_as_effect_output`, `..._as_effect_input`, `..._as_effect_failure`. They keep the boundary.
- **Conflict (medium):** `test_constructor_type_in_an_effect_output_field` (step 3) asserts the D6B-19 text for `P.n: NonZeroInt`, an output field. S3 lifts exactly that position. `NonZeroInt` has an Int parameter, which S4 excludes. The spec does not say the reject for an Int-parameter constructor in an output field, and does not name the step 3 test change. If GREEN keeps D6B-19 for that case, the stale "interim" text stays. If not, the step 3 suite fails at TEST. Decide the text and list the step 3 test change in the spec.

## Answers to the review questions

| Question | Answer |
|---|---|
| All 6 fail for the missing behavior | 3 of 6 yes (the two `--stored` rejects, D6B-50). 3 of 6 fail for the wrong fixture (objection 1). |
| Partial GREEN: enum decode, no record constructor | Caught: `amount_constructor_failure_is_typed_reject`, `test_stored_record_fails_the_record_constructor`. `amount_constructor_accepts` alone passes, because the raw map equals the record value. |
| Partial GREEN: no `--stored` check | Caught by the two `--stored` reject tests. |
| Partial GREEN: no `unknown_fields` flag | Caught by `other_status_is_unknown`, `record_keeps_unknown_fields`. |
| All three only after objection 1 | Yes. Today the runtime checks run against the step 7 fixture. |
| DL-099 B at runtime | Yes: keys inside `state` (a top-level read finds no key and fails), scalar `"ok"` and `replay_scalar`. |
| DL-085 at runtime | Not between signatures (objection 3). |
| `state.extra` against D6B-49 and DL-099 | Consistent. `code` is declared by D6B-49, never a key by DL-099; only `state.extra` is reported (P6). |
| Struct order fault | Step 2 defect, not step 8. Fix and test first (objection 2). Existing EFFECT fixtures not affected. |

## Other false-pass risks

- **[Observed]** `test_stored_records_pass_the_constructors` checks only `stderr == ""`. It does not check that the constructor check ran. The two reject tests cover this.
- **[Inference]** `stored-fail.jsonl` record 3 also has a bad `amount`; the count `2` catches a check that stops at the first failure.

## Limits

- The probe and the scan live in the scratch directory only.
- No GREEN was simulated. The objection 1 outcome after GREEN is an inference from the fixture and snapshot contents.
