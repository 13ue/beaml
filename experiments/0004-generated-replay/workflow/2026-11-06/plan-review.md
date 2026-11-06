---
id: experiment-0004-plan-review
kind: review
status: pending
updated: 2026-11-06
---

# Plan review: EXPERIMENT 0004 (Devil's Advocate, spec mode)

**Target.** [README](../../README.md), [syntax-options.beaml](../../syntax-options.beaml), [plan](plan.md).
**Context read.** 0003 README and gate ledger, 0002 `replay.ex`, `router.ex`, `payment_http.ex`, `probe_support.ex` (`valid_payment!`), 0003 `replay_run_test.py` (constants and harness), roasting round 3 objection 4, `wiki/sources/baml-v1.md`.

## Verdict

**BLOCK.** One critical, two high. Resolve objection 1 before the owner answers Q1. The syntax choice depends on what the discriminating case is.

**[Verified]** Fair statement of the plan. Cases (a)–(c) do test the literal owner requirement: the compiler emits the runner and the host file is deleted. The plan already says that a shared Elixir library can pass (b)–(d). It names (e) as the case that separates the language claim.

## Objections

### 1. Case (e) does not separate the language claim. The 0003 hand-written runner already passes most of it

Category: premise and specification quality. Severity: **critical**. Disposition: pending. Disposition rationale: null.

- **[Verified]** [`replay.ex`](../../../0002-http-correlation/apps/orders_api/lib/orders_api/replay.ex) contains no SCHEMA fact. It checks operation, attempt, request equality with `OrdersBeamlSpike.prepare/1`, status and digest. Then it calls the regenerated `OrdersBeamlSpike.finish/1`. A new field on `Payment` changes only generated code and `valid_payment!/2`.
- **[Inference]** So "zero edits to replay code" in case (e) is true today, for the hand-written runner, with no compiler work. The 8 cases on new records then pass when Payments sends the new field.
- **[Inference]** The only part of (e) that the 0003 runner fails is the typed reject of an old record. Every Q4 answer is generic, not per SCHEMA: (i) compare a SCHEMA version in the record, (ii) compare `artifact_id` with `ProbeSupport.beam_hash/1`, or rescue the `finish` input check. A shared library adds this once, with the same descriptor.
- **[Verified]** The README claim "Case (e) is the case that separates the language claim" has no supporting check. Round 3 objection 4 asks for a comparison against Elixir with equal helpers. The plan moves that comparison after 0004.

**Consequence.** 0004 can pass all five cases and still not show that the language does more than a 40-line shared helper. The owner goal "no team rebuilds it per codebase" is also met by a library. The outcome (no per-codebase runner) does not need the mechanism (compiler generation). The plan does not test which one gives fewer manual change sites.

**Smallest resolving test.** Before any compiler work, run case (e) against the unchanged 0003 runner plus a generic `Replay.run(descriptor, ...)` helper. Count manual change sites. If both pass with zero replay edits, (e) is not a discriminator. Then name a case that only declaration-derived code passes. Candidates: a request or response TYPE change that a descriptor does not see, or a declaration/CAPTURE drift that fails at compile time, not at test time.

### 2. "Generated, no host replay code" excludes CAPTURE, hooks and the artifact check by definition

Category: scope and specification quality. Severity: **high**. Disposition: pending. Disposition rationale: null.

- **[Verified]** CAPTURE in [`payment_http.ex`](../../../0002-http-correlation/apps/orders_api/lib/orders_api/payment_http.ex) (`capture/3`) exists only for replay. It hard-codes `operation: "payments.authorize"`, `attempt: 1`, `version: 1` and the field set. The plan puts CAPTURE generation out of scope.
- **[Verified]** Case (d) says "the host adds only the live transport and CAPTURE for it" and then measures "zero replay lines". CAPTURE lines are replay lines. The measure "every host function the runner calls is also called on the live path" passes for `capture/3`, because the live path calls it.
- **[Verified]** The declared `record { request, status, body }` constrains only the reader. The writer is hand-written per EFFECT. The plan covers the drift with a test that reads both literals (Decision table, "Operation name source in CAPTURE"), not with the compiler.
- **[Inference]** Q2 (ii) hooks argument and Q3 (ii) caller-side artifact check put replay wiring into every caller. In 0004 the test harness is the only caller, so the host diff stays empty. A real codebase must write that call site.

**Consequence.** A pass shows "half of replay is generated". Each team still writes and keeps in sync the CAPTURE record, the hooks map and the artifact check for each EFFECT. That is the per-codebase work the owner wants to remove.

**Smallest resolving test.** Count CAPTURE, hooks wiring and artifact check as replay lines in cases (c) and (d). The smallest change that can pass: generate a record function (for example `OrdersBeamlSpike.Replay.record(request, status, bytes)`) from the same declaration. The host transport calls it in one line. Then operation, attempt and fields have one source.

### 3. Options A and C allow a template emitter to pass (a)–(d). A smaller first slice exists

Category: alternatives and implementation. Severity: **high**. Disposition: pending. Disposition rationale: null.

- **[Verified]** The first failing test checks literals in stdout: `defmodule Replay do`, `def run(`, `payments.authorize`, six atoms. The record fields `request, status, body` are transport fields, the same for every HTTP EFFECT. They are not BEAML TYPES, so the compiler has nothing to check them against.
- **[Inference]** An emitter that pastes the 0003 `replay.ex` text into `main.rs` with three literals replaced passes (a)–(c). This derives nothing. The per-codebase runner moves into the compiler as a string.
- **[Verified]** The 0003 harness hard-codes `ORDER`, `PAYMENT`, `OPERATION` and `STUB_BODY` (`replay_run_test.py` lines 26–31). Case (d) "the same 8-case matrix" for a second EFFECT needs more than "runner entry parameter only".
- **[Proposal]** Smaller first slice: case (a) + (b) only, one EFFECT, plus the objection 1 comparison. Defer (d). It needs new host transport and CAPTURE, and it adds no derivation evidence beyond (a).

**Consequence.** The owner may choose A or C, see GREEN on (a)–(d) and read it as derivation. The second EFFECT costs a full host transport for no new evidence.

**Smallest resolving test.** Add a negative case to (a): change the request TYPE of `prepare` or the input TYPE of `finish` without a change to the EFFECT declaration. Expect a compile error, or a changed generated check. A template emitter fails this. A real derivation passes it.

## Syntax options: strongest risk

- **A (`effect` block).** Template false pass: the block holds literals and two function names; little forces real derivation.
- **B (`extern fn` with flow).** Highest cost: router changes, so 0003 live evidence must run again before any replay result counts.
- **C (attribute).** Most likely false pass: a literal descriptor inside a comment-like attribute, the same as a hand-written Elixir descriptor (the README already says so).

## Deliberately not challenged

- **Nested `Replay` module.** One stdout and the 0002 rename make it the cheapest choice.
- **Six atoms kept.** Case (b) must compare against the 0003 baseline unchanged.
- **D001 and D002 out of scope.** The plan marks them as owner questions; no failure follows now.

**Not inspected.** The 0001 compiler emit path in full, the 0003 replay notes and review, `run.py`, D002 text and the BAML raw captures. No code ran.

## Disposition (main agent, 2026-11-06)

**[Verified]** The main agent accepts objections 1, 2 and 3. The plan is revised (revision 2). This section records the disposition only; it is not an owner decision on Q1–Q5.

- **Objection 1 (critical): accepted.** Changes: a comparison arm LIB (generic Elixir library and hand-written descriptor), built and tested first as a kill switch. A deciding case DRIFT (DRIFT-R, DRIFT-N, DRIFT-Q) with outcome classes and manual change sites per arm. A stated pass rule and reject rule. Old case (e) and its old-record policy (Q4) move to slice 2. See [README, Comparison arm LIB](../../README.md#comparison-arm-lib) and [Pass and reject rule](../../README.md#pass-and-reject-rule).
- **Objection 2 (high): accepted.** Changes: the generated output covers CAPTURE through `Replay.record/3`. CAPTURE, hook wiring, the runner call site and caller-side artifact checks count as replay lines in both arms. See [README, Replay lines and manual change sites](../../README.md#replay-lines-and-manual-change-sites) and Q2, Q3.
- **Objection 3 (high): accepted.** Changes: recorded fields are typed in BEAML and checked against the TYPES of `prepare` and `finish`. Case (a) has five negative declarations and a template control. Slice 1 is case (a), case (b) and DRIFT on one function; the second EFFECT (old case d) moves to slice 2. See [README, Slice 1](../../README.md#slice-1-acceptance-cases-in-order), [Syntax options](../../README.md#syntax-options) and [plan.md](plan.md).

**[Unknown]** The revised plan has no new review round. A new round needs new evidence (skill rule "One round").

## Review of revision 3

**Target.** [README](../../README.md) revision 3 (slice 1), [plan](plan.md). Mode: spec. Owner decisions (2026-11-06) not reopened.
**Context read.** 0001 `main.rs` (structure, emit), 0002 `router.ex`, `payment_http.ex`, `replay.ex`, `probe_support.ex` (`valid_payment!/2`), `query.py`, `run.py` (H03, H04), 0003 `run.py`, `replay_run_test.py`, `response_capture_test.py`, `trace_lookup_test.py`.

### Verdict

**BLOCK.** One critical, two high. Revision 3 answers objections 2 and 3 of round 1 (generated `record`, typed fields, negative checks). The remaining gap: the pass rule depends on how weak the LIB worker makes LIB.

### 1. The pass rule can be met by a LIB form that the README itself prescribes

Category: specification quality and premise. Severity: **critical**. Disposition: pending. Disposition rationale: null.

- **[Verified]** The LIB descriptor holds "recorded request and response keys" (README, Comparison arm LIB). A response key list duplicates the `Payment` TYPE. DRIFT-R and DRIFT-N then need descriptor edits in LIB and none in GEN. Pass clause (1) holds by construction.
- **[Verified]** The generic `rescue` around `finish` is "permitted", not required. Without it, an old record after DRIFT-R or DRIFT-N crashes in the exact generated `finish` pattern. GEN gives `PaymentError{reason: "decode"}`. Pass clause (2) holds by construction.
- **[Inference]** The README's own [Inference] says a whole-value LIB with a generic `rescue` has no stale descriptor and detects DRIFT-R and DRIFT-N. DRIFT-Q is a `request_mismatch` in both arms: LIB encodes the whole request (`ProbeSupport.json(request)`) and compares it with the generated `prepare/1`. So against the strongest LIB, the reject rule probably applies. Against a weak LIB, the claim passes. The verdict depends on a free choice of the LIB worker.

**Consequence.** Slice 1 can report "language claim holds" while a 60-line library with no key list and one `rescue` is equal or better.

**Smallest resolving test.** Fix the LIB form before GEN results exist: no TYPE-derived key list in the descriptor, a mandatory generic `rescue` that returns a typed reason. Or run DRIFT against both LIB forms and apply the pass rule against the stronger one only.

### 2. The 0003 assertion table is incomplete, and the GEN live evidence is weaker than the control

Category: specification quality and risk. Severity: **high**. Disposition: pending. Disposition rationale: null.

- **[Verified]** `trace_lookup_test.py` line 175 asserts `len(checked["logs"]) == 2 * call`; line 184 records `"logs": 4`. `0003/run.py` runs this test. Removal of `payment_request_prepared` breaks both lines. The README table does not list them, and case (c) says "No other assertion changes".
- **[Verified]** After the removal, Orders writes no log. The 0002 H04 `missing_log` control deletes a Payments log line only. So no test checks Orders log correlation in GEN. LIB keeps it.
- **[Inference]** The root parameter alone cannot select the changed assertions in `replay_run_test.py` (`WATCHED`, `HARNESS`, control result). The 0003 test files need an arm switch. An error in that switch can run the GEN expectations at the default root, and the control run still shows GREEN.

**Consequence.** Case (c) fails as specified, or the implementer edits unlisted assertions. GEN passes (c) with less evidence than the control.

**Smallest resolving test.** List every changed assertion by file and line (include `trace_lookup_test.py` 175, 184). Keep the GEN overlay out of the 0003 test files: copy them into the overlay and diff them against the 0003 originals. Require the diff to equal the table. Either generate one Orders log in `place`, or record "no Orders log" as a lost check in the verdict.

### 3. The owner requirement "typed error on a type mismatch, live and in a REPLAY RUN" has no asserted case

Category: scope. Severity: **high**. Disposition: pending. Disposition rationale: null.

- **[Verified]** Owner decision: "A response that does not match the type gives a typed error, live and in a REPLAY RUN."
- **[Verified]** All 8 cases of (d) carry a valid `Payment` body or fail before decode (the digest case keeps a valid `Payment`). The 0003 live tests cover success and a refused port (`transport`) only. In (f), DRIFT changes both BEAML files, so the live Payments response always matches. The pre-change record is an observed outcome class, not an asserted expectation.
- **[Inference]** `reason: "decode"` and `reason: "status"` are never asserted, live or in replay. A generated decode that accepts extra keys, or a `place` that calls `finish` after a failed step, passes (a)–(e).

**Consequence.** One explicit owner requirement and the runtime half of the pipe rule ("the pipe stops") stay untested. Pass clause (2) may then rest on an untested decode.

**Smallest resolving test.** Add two asserted cases. Replay: a record with a correct digest and body `{"order_id":"order-1"}` gives `{:error, %PaymentError{reason: "decode"}}` with `finish/1` count 0. Live: the existing 0003 loopback stub returns a body with an extra key, then a 503. Expect 502, client span `outcome: "error"`, one RESPONSE RECORD, `finish/1` not called.

### Deliberately not challenged

- **Compiler size for one slice.** About 1,040 lines today; the new emit is large but bounded. "No verdict" covers a failed implementation.
- **Template control by text search.** Weak, but objection 3 of round 1 now has the negative checks in (a).
- **Span rename and `PaymentError` shape.** Owner decisions and Q6 cover them.

**Not inspected.** `trace_lookup_repair_test.py`, `run_test.py` in full, `probe_support.ex` `span/5` body, the 0001 emit of exact map patterns. No code ran.

### Disposition (main agent, 2026-11-06)

**[Verified]** The main agent accepts objections 1, 2 and 3 of this review. The plan is revised (revision 4). This section records the disposition only; it is not an owner decision.

- **Objection 1 (critical): accepted.** Changes: the plan fixes one LIB form, the strongest fair library. Its descriptor has no key list; LIB records whole values; a mandatory `rescue` around decode and finish returns `%ReplayLib.Error{}`. LIB passes (e) and is frozen by SHA-256 before GEN results of (d2) and (f) are judged. The pass and reject rule uses only this LIB; no weak form is built. See [README, Comparison arm LIB](../../README.md#comparison-arm-lib) and [Pass and reject rule](../../README.md#pass-and-reject-rule).
- **Objection 2 (high): accepted.** Changes: the table lists every changed line by arm, file and line number. GEN and LIB run copies of the 0003 tests and `query.py` in a temporary tree with the repository layout; `overlay_diff_test.py` requires the copy diff to equal the table. The originals stay the control. GEN emits `payment_request_prepared` under `orders.prepare`, and LIB keeps the router log, so `query.py` line 17 and `trace_lookup_test.py` lines 175 and 184 stay unchanged. See [README, 0003 lines that change in the arm copies](../../README.md#0003-lines-that-change-in-the-arm-copies).
- **Objection 3 (high): accepted.** Changes: new case (d2) with R1 (replay, body without `status` → `PaymentError` "decode"), R2 (replay of the L1 record), L1 (live extra key → reject, [Proposal]), L2 (live 503 → HTTP 502, error span, one record) and P1 (pipe stop). Each case asserts `finish` count 0. `Replay.record/3` now comes before the status check. See [README, Case (d2)](../../README.md#case-d2-type-mismatch-cases) and [plan.md](plan.md).

**[Unknown]** Revision 4 has no new review round. A new round needs new evidence (skill rule "One round").
