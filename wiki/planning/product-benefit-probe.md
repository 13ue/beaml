---
id: planning-product-benefit-probe
kind: experiment-proposal
status: proposed-not-adopted
updated: 2026-11-05
---

# Smallest product-benefit probe

**[Proposal]** Test whether a small typed program retains useful failure evidence without manual instrumentation at each function.
This tests a product hypothesis. It does not establish that a new language is necessary.
[Conversation and research capture](../../raw/requirements/2026-11-05-product-benefit-followup.md), [source note](../sources/roasting-rounds.md)

## Benefit and comparison

**[Inference]** A shared TYPE declaration could connect boundary checks, error details and source-linked observations.
That could reduce the places an author must update when a program changes.
The key benefit would be less manual coordination with equivalent behavior, not fewer generated lines.
[BAML evidence and limits](../sources/baml-documentation.md#product-benefit-follow-up)

**[Proposal]** Compare BEAML with idiomatic Elixir using shared validation and tracing helpers.
Implement the same behavior and evidence contract on both sides. Do not duplicate helpers at every Elixir call site.
Separate one-time framework/compiler work, application declarations and per-change manual edits.

## One bounded use case

**[Proposal]** Use synthetic support-ticket data through three operations: receive, classify and route.
Replace the provider with one controlled stub. The stub can return a valid classification or a nested invalid value.
Classify output must pass the declared checks before a simulated route effect increments its counter.
Do not infer factual correctness from a structurally valid classification.
Candidate owners: LANGUAGE/COMPILATION for generated checks and source references; EXECUTION for boundary outcomes and simulated effects.
OBSERVATORY receives permitted observations. This proposal does not select an observability service.

Define the small evidence contract before implementation:

- Logical call identity, parent identity and source location for the three operations.
- One terminal success or failure per started operation during the supported normal-completion cases.
- A TYPED ERROR for invalid output, with field path and expected TYPE. Do not compare display strings alone.
- Synthetic input and stub outcome plus exact artifacts for isolated reproduction of that boundary failure.
- Reproduction compares the error variant, field path and source target and performs zero live provider calls or route effects.

The current POC uses fixed ArgumentError messages. It does not yet implement this TYPED ERROR or trace contract.
Runtime function observations are distinct from the existing CLI action log.

## Acceptance and change test

**[Proposal]** Both implementations must pass the same cases:

1. Valid classification selects the expected route and increments the effect counter exactly once.
2. Nested invalid classification reports the expected TYPED ERROR and leaves the counter at zero.
3. Recorded synthetic evidence reproduces that rejection in isolation without live effects.
4. Add one nested function through the supported normal definition path. Repeat success and failure cases.
5. The new function appears in the causal record without manual tracing wrappers or catch-and-rethrow code in BEAML application functions.

Compare handwritten instrumentation sites, required manual edits and evidence completeness against the declared contract.
Count code only as a secondary measure; include declarations and configuration on both sides.
A compiler that hides missing evidence behind a small function fails this test.
Equivalent results with equivalent Elixir author effort leave the proposed language benefit unestablished for this use case.

## Scope and outcome limits

**[Requirement]** The owner later expanded the concrete product scenario to HTTP-separated applications with correlated order-level search and replay.
The [distributed proposal](distributed-order-probe.md) records that scenario. This earlier local proposal remains unexecuted history.

**[Unknown]** No implementation, run, comparison result or owner adoption exists for this proposal.
It is not a registered EXPERIMENT. Select and bound it through the [R&D process](research-and-development.md) before implementation.
No live model, UI, general JSON parser, streaming, retry engine or general foreign-function interface is required by this proposal.
Supported capture scope excludes arbitrary concurrency, process crashes and storage failure; do not call it full typed replay.
This probe can show one useful integration. It cannot prove flawless execution, agent productivity or general superiority over libraries.
