# Slice 6b mini-step struct-order: REVIEW

Fresh-context REVIEW, 2026-11-07, HEAD `fac6d5ac`. Not a Devil's Advocate. Target: [spec.md](spec.md), [notes.md](notes.md) (M1 to M5, GREEN G1 to G3, open point P2), the step 8 RED review objection 2 ([../slice6b-decode-constructor/red-review.md](../slice6b-decode-constructor/red-review.md)), and `git diff 3a4522b0..HEAD` of `main.rs` and `tests/slice6_struct_order_test.py`. TEST evidence: [test-output.log](test-output.log), [test-result.json](test-result.json).

**Verdict: PASS.** Two notes, no block.

## Step coverage (observed)

| Spec item | Result |
|---|---|
| Probe (EFFECT plus `fn check ... ! Bad`): compiler exit 0, `elixirc --warnings-as-errors` exit 0 | met; `slice6_struct_order_test` 2 of 2 OK |
| Guard: `arms/gen/orders.beaml`, `slice2/reuse/orders.beaml` sha256 | met (guard test) |
| Guard: `payments.beaml` equal to the snapshot | met (guard test and `run.py`) |
| Pure modules keep their output | met; `slice6_failure_test` 22 OK (step 2) |
| No change to struct texts or clause texts | met; the diff moves `emit_structs` calls only (filter argument) |

The change is small (+12 −7): one filter on `emit_structs` and one helper `effect_failure`. Nothing beyond need.

## Adversarial probe: gap P2 (observed)

Source (scratch directory):

```
type Order { order_id: String }
fn check "" -> String ! PaymentError = PaymentError { reason: "x" }
fn check x: String -> String ! PaymentError = x
type Payment { order_id: String }
type PaymentError { reason: String }
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")
fn place order: Order -> Payment ! PaymentError = order |> payments.authorize
```

- Compiler with `--stored stored/empty.jsonl`: exit 0, no stderr.
- `elixirc --warnings-as-errors` with the step 7 stubs: exit 1. `error: BeamlSpike.PaymentError.__struct__/1 is undefined, cannot expand struct BeamlSpike.PaymentError` at line 23, `defp __beaml_check(<<>>), do: {:error, %__MODULE__.PaymentError{reason: <<120>>}}`. The `defmodule PaymentError` stands at line 107.
- So the gap fails today, as G3 says.

**Class: Repair.** The fix is inside the compiler and changes no stored data. **[Inference]** A fix that moves every EFFECT failure struct to the top changes the guarded orders bytes; a fix that moves it only when a pure clause body builds it needs a body scan.

**Acceptable until step 8, with a condition.** Reasons:

- **[Observed]** No fixture builds an EFFECT failure struct in a pure fn (scan of 74 `.beaml` sources, see Limits).
- **[Observed]** The step 8 fixture `slice6/decode-ctor/orders.beaml` uses `! NoCurrency` (not an EFFECT failure). The mini-step fix covers it.
- **[Observed]** The fault is loud: `elixirc` stops with a compile error. It is not a wrong runtime result.
- Condition: the first source that has this shape gets the P2 probe as a RED test first.

## Consistency

- RED: 1 FAIL (the probe), 1 PASS (guard); the failure is the missing behavior. GREEN: 2 of 2 OK. TEST rerun: 2 of 2 OK.
- G1 closes P1 (guards PASS because the orders fixtures name `PaymentError` only through the EFFECT).

## Notes

**N1 (medium, process).** This ledger has no own `red-review.md`. The RED probe comes from the step 8 RED review (objection 2), and notes.md records a control run and a hand-fixed copy. This review confirms the RED as genuine: the probe class reproduces (P2 above gives the same error form). Minimum repair: none required; the next mini-step gets its own RED review.

**N2 (medium, Repair).** The spec fix contract says "In every module, each struct module of a failure TYPE comes before its first use". GREEN meets it only for failure TYPES that no EFFECT names (G3). Minimum repair: a line in spec.md or notes.md that the contract is met except P2, with the probe above as the next test.

## Decisions of this review

- **R1 · Repair.** **Chose:** accept gap P2 until a source needs it. **Over:** close it now. **Because:** no fixture and no step 8 source has the shape, the fault is a loud compile error, and a fix needs a body scan or a guarded byte change. **Commits us to:** the P2 probe becomes a RED test before any source with this shape.
  By: Opus (REVIEW, slice6b-struct-order)
- **R2 · Undo.** N1 and N2 are notes, not blocks.
  By: Opus (REVIEW, slice6b-struct-order)
- **R3 · Undo.** The TEST log of this ledger references the step 7 TEST log for the shared runs.
  By: Opus (REVIEW, slice6b-struct-order)

## Limits

- The probe ran with stubs, not a release.
- The fixture scan is a text search over 74 `.beaml` files outside `results/` and `target/`: for each EFFECT failure name, a line other than `effect`, `type` or `enum` with `= ... Name {`. 0 hits. A multi-line clause body is not seen by this scan.
