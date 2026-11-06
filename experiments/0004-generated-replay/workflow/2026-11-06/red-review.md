---
id: experiment-0004-red-review
kind: review
status: disposed
updated: 2026-11-06
---

# RED review: EXPERIMENT 0004, slice 1 (Devil's Advocate, code mode)

**Target.** Commit `4dc9cdd` and the `tests/cli.rs` tests of commit `49aedb9`. Spec: [README](../../README.md) revision 4 with the owner decisions (2026-11-06), [plan.md](plan.md), [plan-review.md](plan-review.md), [notes.md](notes.md) sections "RED" and "RED check (main agent)". Owner decisions are not reopened.

**Evidence.** **[Verified]** The SHA-256 values of `cli.rs`, `arms_test.py`, `arm_tree.py`, `drift_test.py`, `overlay_diff_test.py`, the snapshot, the `run.py` stub and `arms/gen/orders.beaml` equal the table in notes.md. The retained run `results/20261106T114911001663Z` shows 14 failed and 1 passed, as recorded. No test ran again.

## Verdict

**BLOCK.** Three high objections. Each failure is a real missing-behavior RED today (lexer stop, missing overlay copies, missing LIB, `run.py` stub). The guards are sound. But one test can pass for a template emitter, the (d2) set does not match the restated owner decisions, and the LIB form test cannot detect a weak LIB. Repair the tests, record the new SHA-256 values, then start GREEN-1.

**[Verified]** Safeguards that hold: the negative CLI tests reject the old parser message and require the named tokens (`cli.rs` `assert_rejected`); `undeclared_failure` requires `payments.authorize` and `PaymentError`; the overlay diff test checks line count, the exact changed-line set and the line text per row; P1 counts `prepare/1` and `finish/1` with `call_count` traces; R1 and R3 assert `finish/1` 0, `valid_payment!/2` 0, transport 0; L2 asserts 0 `orders.finish` spans; the (c) and (e) runners refuse to start without the arm copies, so the control cannot pass for an arm.

## Objections

### 1. The template control passes on the current emit path; a fixed decode passes slice 1

Category: implementation. Severity: **high**. Disposition: pending. Disposition rationale: null.

- **[Verified]** `cli.rs:304–316` checks `mentions(&drift, "reference")` over the whole stdout, not over the decode. README case (b) requires "the generated decode must contain `reference`".
- **[Verified]** The 0001 emitter already writes every interface field into `__beaml_valid__` and every pattern key into the `fn` clause (`tests/payments.generated.snapshot` lines 6 and 15, byte-list form). `drift/R/orders.beaml` line 9 makes `finish` read `reference`. `mentions` accepts the byte-list form (`cli.rs:124`).
- **[Inference]** An emitter with a hard-coded `order_id`/`status` decode passes this control through `finish/1` and `__beaml_valid__` alone. All (d2) cases use the base `Payment`, and (f) records outcomes without assertion. No asserted test then sees a template decode.

**Consequence.** The round 1 objection 3 control (template versus derivation) is void. GREEN can paste a decode string and pass (a)–(d2).

**Smallest fix.** Name the decode function in the plan (for example `defp __beaml_decode_payment`). In `cli.rs`, slice the DRIFT-R stdout from that `def` to the next `def` and require `reference` inside the slice. Require it to be absent in the base slice. A stronger option: one asserted replay case in a DRIFT-R tree, where a record without `reference` gives `PaymentError{reason: "decode"}`.

### 2. Case (d2) does not match the restated owner decisions: no live decode error, and R2 asserts the superseded D7 shape

Category: scope and specification quality. Severity: **high**. Disposition: pending. Disposition rationale: null.

- **[Verified]** Owner decision: "A response that does not match the type gives a typed error, live and in a REPLAY RUN." After the change to tolerant decode, L1 became an accept. The live cases are L0 (valid), L1 (accept), L2 (status 503). No live case sends a missing or wrongly typed field (`arms_test.py:364`). The decode error is asserted only in replay (R1, R3).
- **[Verified]** The RED check (notes.md, "RED check (main agent)") repairs D7: `Replay.run/3` has one return shape `{:ok, payment}`; the hint goes on the replay EFFECT span. The committed harness still accepts `{:ok, p, hint}` (`arms_test.py:80`, `:90`), and R2 expects `{"ok": PAYMENT, "hint": {...}}` (`arms_test.py:423`). The harness reads no spans in the eval VM.
- **[Inference]** A GEN that follows the repaired D7 fails R2 forever, so GREEN must edit a frozen RED test or break D7. A GEN with the decode only inside `Replay.run/3` and a raw pattern match on the live path passes every (d2) case. The live missing-key response then crashes Orders without a typed reason. The README sentence "Live and replay use the same decode" has no asserted check.

**Consequence.** One half of an owner requirement (typed error live) is untested. The replay hint is checked in one place only, and in the form that the main agent rejected.

**Smallest fix.** Add L3: the stub returns 200 with `MISSING_KEY_BODY`. Expect HTTP 502, client span `outcome: "error"`, one RESPONSE RECORD with byte-exact bytes, 0 `orders.finish` spans. Change R2 to expect `{"ok": PAYMENT}` and read `unknown_keys == ["fraud_score"]` from the replay `orders.payments.authorize` span in `out/spans.jsonl` (`PROBE_OUTPUT` is already set). Remove the 3-tuple branches from `HARNESS`. If the eval VM writes no span (README [Unknown]), record that as a table change before GREEN.

### 3. The LIB form test cannot detect a weak LIB, so pass clause (2) can hold by construction again

Category: risk. Severity: **high**. Disposition: pending. Disposition rationale: null.

- **[Verified]** The mandatory typed rescue is checked by the text `"rescue" in lib` (`arms_test.py:453`). R1 and R2 on LIB are only saved (`arms_test.py:483–495`). Then the freeze accepts any hash in `freeze.json`.
- **[Verified]** README: `ReplayLib.run` "wraps decode and finish in one `rescue`. It returns `{:error, %ReplayLib.Error{step, reason}}`, never a raise."
- **[Inference]** A LIB with `rescue` in a comment, a re-raise, an untyped tuple, or a `rescue` around decode only passes (e) and is frozen. LIB R1 is the exact finish-step failure: the generated `finish` clause does not match a body without `status`. After DRIFT-R and DRIFT-N, a weak LIB crashes on the pre-change record. The owner rule counts that as a miss. GEN then wins clause (2) by construction. This is the revision 3 critical objection 1, now reachable through the test.

**Consequence.** The verdict again depends on a free choice of the LIB worker, and the frozen hash makes the weak form permanent for (f).

**Smallest fix.** Before the freeze, assert the LIB R1 result is `{"error": ...}` and starts with `%ReplayLib.Error{step: "finish"` (or `"decode"`). This asserts the fixed form ("never a raise"), not an outcome class, so the README rule "outcomes recorded, not asserted" stays true for L1, L2 and R2.

## Answers to the review questions

- **Genuine RED.** Yes for all 26 failures; all fail on missing behavior, none on a setup error (run 1 excluded correctly).
- **Fixed template.** Can pass. Objection 1.
- **Compiler that special-cases fixture names.** The negative tests accept any message that names the token; a lookup by fixture text could pass. Bounded by the (b) emit and the live runs; not raised.
- **LIB built weak.** Can pass. Objection 3.
- **Test copies drift from the change table.** Not possible without a failure: exact changed-line set, line count and row text are checked.
- **Hint in one place.** Live: record and span (L1). Replay: return value only, in the rejected form. Objection 2.
- **Pipe stop.** Observed: P1 by `call_count`, L2 by spans, R1 and R3 by `finish/1` 0.
- **Two-step GREEN.** Sound, with one condition. Case (b) checks only names (`:json.decode(`, `def run(`). GREEN-1 must stop at that shape. If GREEN-1 writes the full decode, the "fresh RED of (d2)" is a post-hoc pass, not RED. Record per case the failure reason after GREEN-1 (for example R1 `ok` instead of `decode`).

## Deliberately not challenged

- **Owner decisions.** Tolerant decode with hint, typed `PaymentError` with `reason`, one `!` TYPE, LIB in parallel: authority, no new evidence.
- **DRIFT outcomes recorded, not asserted.** README rule; the pass and reject rule judges them.
- **Freeze order "before GEN is judged".** Not testable by a hash; process rule for the gate ledger.

**Not inspected.** The 0003 test bodies beyond the table lines, `probe_support.ex` `span/5`, the 0001 compiler source beyond its emit sample, `red-output.log` in full. No test ran.

## Disposition (main agent, 2026-11-06)

- **Objection 1: applied.** The decode has the fixed name `__beaml_decode_payment/1`. `cli.rs` slices the decode body and checks field names there only. Base and DRIFT-R checks changed; new asserted test on DRIFT-N (rename `status` → `state`).
- **Objection 2: applied.** New live case L3 (200 without `status`): HTTP 502, span `orders.payments.authorize` with `outcome: "error"` and `reason: "decode"`, one RESPONSE RECORD, 0 `orders.finish`, transport 1. `HARNESS` has one return shape (D7 repair). R2 expects `{:ok, payment}` and reads `unknown_keys` from the replay EFFECT span in the replay report. A probe showed that an eval VM can write the span; no table change.
- **Objection 3: applied.** Before the freeze, LIB R1 must be `%ReplayLib.Error{step: "decode" | "finish", reason: ...}`. The `rescue` text check stays as a guard only.
- **Review condition: accepted.** GREEN-1 stops at the shape that case (b) checks. After GREEN-1, record per (d2) case its own failure reason before GREEN-2.
- Evidence: notes.md, section "RED repair"; red-output.log, section "RED repair after the RED review". New SHA-256: `cli.rs` `bf2b82fd…`, `arms_test.py` `c0f35e8f…`.
