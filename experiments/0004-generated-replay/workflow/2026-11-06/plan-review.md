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
