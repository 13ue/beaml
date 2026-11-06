---
id: planning-distributed-order-probe
kind: experiment-proposal
status: proposed-not-adopted
updated: 2026-11-05
---

# Distributed order product-benefit probe

**[Requirement]** The owner wants searchable, correlated cross-application evidence and replay over REST boundaries.
The [source note](../sources/distributed-order-requirement.md) records the target and evidence limits.
This scenario extends the earlier [local product-benefit proposal](product-benefit-probe.md); it is not an executed replacement.

## One synthetic order through three applications

**[Requirement]** The owner subsequently requested an exact plan for discussion before implementation.
**[Verified]** [EXPERIMENT 0002](../../experiments/0002-http-correlation/README.md) passed its bounded Orders and Payments correlation cases.
The three-application scenario and REPLAY RUN below remain proposals.

**[Proposal]** Start with `orders_api` → HTTP → `payments_api` → HTTP → `inventory_api` in one umbrella repository.
Use distinct local BEAM operating-system processes/releases and ports for the probe. Do not use direct sibling-module calls.
An umbrella is a source/build organization; the process and deployment boundaries need explicit configuration.
Local HTTP is sufficient to test propagation. It does not establish TLS or production deployment behavior.
No broker, live payment, LLM or general observability platform is required for this probe.

## Product hypothesis

**[Inference]** BEAML could connect TYPE/SCHEMA checks, source references, remote outcomes and domain causality at generated HTTP adapters.
This could reduce manual coordination across separately built applications.
It requires participating adapters and compatible versioned wire CONTRACTS. A compiler cannot see arbitrary remote code from a local function signature.
Foreign Elixir remains supported only within an explicit instrumentation and capture boundary.
This is not a guarantee of network delivery, atomic cross-service commit or factual business truth.

## Correlation without merging meanings

**[Proposal]** Define these distinct references before implementation:

| Reference | Purpose | Limit |
|---|---|---|
| Authorized order reference | Find all relevant runs for one synthetic business order | Not an authorization token; one order can span many traces |
| WORKFLOW RUN reference | Identify one attempt at the overall business workflow | Distinct from the order and individual retries |
| trace/span identity | Correlate a technical call and its permitted logs | Not durable business commitment or complete replay history |
| COMMAND/DOMAIN EVENT identity and causal references | Connect requested work, committed facts and subsequent work | A log or span does not establish a committed DOMAIN EVENT |
| Operation/attempt identity | Distinguish a logical operation from its HTTP retries | Trace identity alone is not an idempotency protocol |
| Artifact and SCHEMA version | Resolve each service's original checks and source | Services need not share one compiler build or schema version |

Propagate W3C trace context through HTTP adapters. Correlate structured logs with their local span where present.
Keep business references in an authorized correlation view. Do not broadcast raw order identifiers through arbitrary baggage.
Use causal edges for ordering; wall-clock timestamps alone cannot establish distributed causality.
Missing context or sampled data must remain visible as gaps.

## Two acceptance paths

**[Proposal]** First verify these paths against a declared small query and capture contract:

1. Successful order: all three services participate, and their permitted traces, logs and committed test events are linked.
2. Timeout path: the payment application may commit its simulated effect before the caller loses the response.
   Keep the caller's observed outcome uncertain. Keep any independently retained payment commitment as separate evidence.

Search by the authorized order reference must return all retained matching traces, correlated logs and domain facts.
Also query a typed failure and show the causal path and per-service source locations.
Include two traces for the same order and a later status request. A single trace lookup is insufficient.
Include a retry with its own attempt identity and assert one simulated business mutation under the chosen deduplication contract.
Do not promise exactly-once delivery from this result.

## Replay is more than a joined search result

**[Proposal]** Record permitted synthetic HTTP requests and observed responses/timeouts, initial state, relevant nondeterministic inputs and exact artifacts.
Keep required REPLAY HISTORY independent of sampled OBSERVATION EVENTS.
For a first bounded REPLAY RUN, replay the orders application's decisions using captured HTTP outcomes.
Replace outbound calls with fixture responses. Assert zero live downstream calls and zero external business mutations.
Compare typed outcome and requested operation/attempt sequence. Missing required evidence must block or report divergence.
This client-side replay does not reproduce payment or inventory internals.
Those services need their own compatible capsules for a later composed replay.
An original timeout remains the recorded timeout even if later evidence establishes the payment's commitment.
Newly combined evidence is analysis; live reconciliation and retries are different operations.
[Replay semantics](../concepts/typed-errors-and-replay.md)

## Fair comparison and state

**[Proposal]** Compare against idiomatic Elixir with OpenTelemetry instrumentation and shared typed-boundary helpers.
Both sides must meet the same correlation, query and replay contract.
Measure manual edits when adding a service or changing a response field, alongside evidence completeness and runtime overhead.
Count generated integration and shared runtime work separately from application code. Do not assume a language advantage.

Candidate owners: LANGUAGE/COMPILATION for descriptors/adapters; EXECUTION for outcomes and capture; OBSERVATORY for permitted search projections.
**[Unknown]** No implementation, owner adoption of this exact probe, latency result or distributed replay result exists.
Search storage, wire contracts, support versions and capture durability remain open.
Register an EXPERIMENT through the [R&D process](research-and-development.md) before implementing the selected scope.
