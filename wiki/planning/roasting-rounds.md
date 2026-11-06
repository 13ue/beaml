---
id: planning-roasting-rounds
kind: review-record
status: open-objections
updated: 2026-11-05
---

# BEAML roasting rounds

The [conversation source](../sources/roasting-rounds.md) records provenance and coverage limits.
These are architecture challenges, not release gates or findings of proven implementation failure.
Human dispositions remain pending unless an explicit decision is recorded below.

## Round 1: reduce the first slice

**[Inference]** The initial slice risked combining too many unsettled concerns before producing useful evidence.
The review also questioned syntax readiness and missing evidence against a plain Elixir-library alternative.
The original full response is unavailable here; no exact severity or complete objection list is reconstructed.

**[Requirement]** The owner then selected a minimal syntax spike and later adopted the initial Elixir backend.
The [syntax source](../sources/syntax-spike-requirement.md) records those separate decisions.
**[Verified]** [EXPERIMENT 0001](../../experiments/0001-syntax-to-beam/README.md) provides evidence for that smaller subset.
It does not establish a workflow benefit over an Elixir library.

**[Proposal]** Resolve the remaining value question with a shared workflow and explicit comparison criteria.
Compare prevented failures and authoring effort. Do not assume either implementation is superior.
Disposition of the broader language-value objection: pending. Disposition rationale: null.

## Round 2: one guarantee across the boundary

**[Proposal]** Central question: which concrete error does BEAML prevent from foreign input to the first domain effect?
Does that guarantee justify the cost of a separate language?

Category: premise and scope. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The POC checks exact shapes and nested patterns and executes generated code on the BEAM.
Its [documented limits](../../experiments/0001-syntax-to-beam/README.md#evidence-and-limits) exclude EFFECT support, provider calls and full typed replay.
The [product CONTRACT](../concepts/product-contract.md#trust-transitions-are-explicit) requires rejected input to cause no domain effects.

**[Inference]** More syntax could extend the compiler without testing that cross-boundary requirement.
This is a gap between current evidence and the product target, not a failure of EXPERIMENT 0001's criteria.

### Proposed invariant and smallest resolving test

**[Proposal]** Within a declared controlled boundary, no domain effect occurs before all required input checks pass.
A VALIDATED VALUE certifies only its named checks. Shape alone proves neither authority nor factual truth.

Use one simulated effect with a call counter:

1. Valid input produces exactly one call.
2. Nested invalid input produces zero calls.
3. The public Elixir entry point preserves both results.
4. Prevent a known bypass or explicitly exclude it from the declared guarantee.

Passing these cases would provide scoped evidence, not a general proof or a language-value comparison.
**[Unknown]** This proposed EXPERIMENT has not been adopted, implemented or run.
Its controlled boundary and required checks still need definition.

### Deliberately not challenged

The accepted syntax and initial Elixir backend remain in place. The review supplied no new reason to reopen them.
No complete code audit or new runtime test was performed during this round.

## Follow-up

### Round 2 clarification: product value is a separate question

**[Verified]** In follow-up discussion, the AUTHORING AGENT corrected its framing of the boundary invariant.
That test alone cannot justify a language; an Elixir library could provide boundary checks too.
The original review remains above as history. No human disposition is inferred from this correction.

**[Requirement]** The owner asks for a concrete product-benefit test and describes a BAML talk about instrumentation growth.
The [follow-up source](../sources/roasting-rounds.md) records the description and its limits.
**[Proposal]** Compare small application functions with equivalent typed failure evidence and source-linked observations.
The [product-benefit probe](product-benefit-probe.md) defines a bounded workflow, fair Elixir comparison and change test.
The proposal is not adopted or executed. The product-value objection remains pending.

**[Proposal]** Select the next EXPERIMENT through the [R&D register](research-and-development.md).
Keep the proposed invariant, executed results and owner decisions separate.
Add later rounds as new records; preserve the original conversation capture.

## Round 3 — Test the competitive claim (2026-11-05)

Spec mode. Target: BEAML's current evidence, the proposed first REPLAY RUN and the claim of a 3–8× advantage over BAML.
The strongest case for BEAML is one checked CONTRACT across a model result, an HTTP boundary and failure evidence.
It could reduce repeated work in Elixir applications that use model output for domain decisions.
See the [conversation and research capture](../../raw/requirements/2026-11-05-roasting-round-3.md).

| Evidence | LANGUAGE/COMPILATION | Host and OBSERVATORY | Result |
|---|---|---|---|
| [0001](../../experiments/0001-syntax-to-beam/results/20261105T202319485083Z/result.json) | Generate Elixir checks for exact shapes and nested patterns | Compile and run the output on the BEAM | Compiler, CLI and BEAM tests passed |
| [0002](../../experiments/0002-http-correlation/results/20261105T221134010042Z/result.json) | Generate three checked fixture functions | Orders → HTTP → Payments. Elixir propagates context, records observations and serves a fixed payment response. | H01–H05 passed, including missing context and missing log controls |
| Proposed next test | Derive validation, typed outcome and capture/replay metadata from one declared boundary | Elixir performs HTTP and capture. A test runner substitutes captured outcomes and counts calls. | Pending |

### 1. The 3–8× claim has no denominator

Category: premise, scope and specification quality. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The [owner's thesis](../../raw/requirements/2026-11-05-roasting-round-3.md) includes breadth in the comparison.
The [R&D register](research-and-development.md) reports no head-to-head result.
**[Inference]** Counting compiler, provider and operations features rewards inventory. It can hide slower changes and more integration work.
A team can add scope and still lose its most important task against a smaller tool.
**[Proposal]** Name the user, workflow and primary measure before the test. Keep coverage and correctness separate from the time ratio.

### 2. BAML is a moving baseline with overlapping features

Category: premise and alternatives. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The established BAML v0 changelog records 0.226.3 on 2026-10-27. Its documentation covers typed structured output and streaming, retries and fallback, tests and per-attempt observations.
The newer language line separately documents typed errors, concurrent tasks and SQL queries over recorded telemetry.
GitHub lists the 0.23.1 nightly series. These are separate observations about docs and release lines.
See the [versioned source details](../../raw/requirements/2026-11-05-roasting-round-3.md#baml-evidence).

**[Inference]** Comparing BEAML to a prompt wrapper would ignore those capabilities. Typed failures and searchable traces alone do not differentiate the tools.
**[Proposal]** Use BAML for one typed extraction and an idiomatic Elixir host for the domain operation. Give the host the same shared tools as the BEAML case.
Pin the BAML build and verify its capabilities in the fixture. Test the newer line separately if it fits the same workflow.

### 3. OTP restarts processes. It cannot settle an uncertain payment

Category: implementation and risk. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** OTP supplies lightweight processes and monitoring. EXPERIMENT 0002 ran separate local BEAM processes with Erlang distribution disabled.
The [Orders](../../experiments/0002-http-correlation/apps/orders_api/lib/orders_api/router.ex) and [Payments](../../experiments/0002-http-correlation/apps/payments_api/lib/payments_api/router.ex) host routers call the observation helper around the generated functions. Payments performs no business mutation.
See the [OTP process reference](https://www.erlang.org/doc/system/ref_man_processes.html) and [independent verification](../../experiments/0002-http-correlation/workflow/2026-11-05/result.json).

**[Inference]** Ordinary Elixir can use the same OTP features. A caller timeout can occur after a remote commit. Restarting or correlating a trace cannot settle that outcome.
TYPE checks also cannot establish who authorized the operation or whether a model result is true.
**[Proposal]** Commit once to an independent test ledger and then lose the HTTP response. Require the caller to preserve the uncertain outcome.
Report the recorded commit separately. An isolated REPLAY RUN must issue zero live requests and make zero live mutations.

### 4. Fixture replay can leave the language claim untested

Category: scope and alternatives. Severity: high. Disposition: pending. Disposition rationale: null.

**[Verified]** The [distributed order proposal](distributed-order-probe.md#replay-is-more-than-a-joined-search-result) limits its first replay to Orders decisions with captured HTTP outcomes. It already calls for gap detection and isolation.
EXPERIMENT 0002 covers fixed loopback correlation and bounded local files.
**[Inference]** A hand-written recorder and fixture player can meet that replay scope. This would answer a useful EXECUTION question and leave the language-value question open.
**[Proposal]** Derive the boundary identity, checks and capture/replay descriptor from one BEAML declaration. Compare a response SCHEMA change and an incident task against Elixir with equivalent helpers.
Reject the language claim for this slice if the advantage disappears when the host baseline uses a shared helper.

### Proposed smallest comparison

**[Proposal]** Use one synthetic model extraction and one HTTP effect in the two existing releases.
Feed each implementation the same raw synthetic model response. Require the same extracted result and downstream decisions.
Use a fixed valid result and one invalid result. Add the response-loss case in objection 3 and a missing-capture control.

Compare BEAML with a generated boundary adapter, idiomatic Elixir with reusable validation and OpenTelemetry helpers, and pinned BAML plus the Elixir host.
Use the documented REST preview or a small supported-SDK bridge for BAML. Record the chosen integration cost. Avoid dependence on the community Elixir binding.
Give each case the same test ledger, replay runner contract and shared dependencies when applicable.
Use no third service. Keep production durability and composed replay outside this test.

1. **Correctness gate.** The valid case has one test commit. Invalid input has zero downstream calls. The lost response yields a TYPED ERROR for the uncertain outcome.
   Replay reproduces the error and the intended operation/attempt sequence with no live calls or mutations. Missing required evidence fails explicitly.
2. **Derivation gate.** Change the response SCHEMA once. Regenerate the checks and source-linked capture metadata, with no manual metadata edits.
   The original artifact must remain usable for the original REPLAY CAPSULE. Reject an incompatible capsule explicitly if its original artifact is absent.
3. **Value gate.** Give independent operators the same brief and fixed incident artifact. Measure active time from receiving the artifact to locating the source and reproducing the typed failure.
   Use a counterbalanced order and report individual times. A small pilot is directional. A 3× result on that task requires the fastest qualifying baseline median divided by the BEAML median to be at least 3.
   Separately record manual change sites and initial compiler, runtime and bridge work. Keep the engineering budget equal. Stop an arm at its time limit and report it as incomplete.
   If correctness holds but there is no repeatable task advantage, keep replay as infrastructure evidence and defer new language scope.
   A task win justifies a wider test. It does not establish a product-wide multiplier.

### Deliberately not challenged

**[Verified]** The initial Elixir backend and the two passed EXPERIMENTS answer their bounded questions.
**[Unknown]** This review did not run a competitor, measure performance, test security or inspect all BAML features. No owner disposition on these objections is recorded.
