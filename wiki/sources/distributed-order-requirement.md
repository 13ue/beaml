---
id: source-distributed-order-requirement
kind: source-note
status: owner-requirement
updated: 2026-11-05
---

# Distributed order visibility requirement

Origin and publisher: repository owner, conversation dated 2026-11-05. Access date: 2026-11-05.
No upstream conversation URL or version applies.
The [selected capture](../../raw/requirements/2026-11-05-distributed-order-observability.md) records coverage, interpretation and selected external references.
Retention follows the owner's documentation instructions. No third-party source text is copied.

**[Requirement]** Support an umbrella-based example with applications separated by HTTP/HTTPS REST APIs and no direct cross-application calls.
Provide search and analysis that correlate traces, logs, events and orders across those boundaries.
Support replay of the surrounding execution. This extends the concrete scenario for the [existing replay target](typed-replay-requirement.md).

**[Inference]** Orders here mean business orders. This is not a new platform BOUNDED CONTEXT.
**[Verified]** OpenTelemetry documents [context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) and correlation of logs with trace/span identity.
Its [baggage guidance](https://opentelemetry.io/docs/concepts/signals/baggage/) does not grant authority to propagated metadata.
[Mix release documentation](https://mix.hexdocs.pm/Mix.Tasks.Release.html) describes application selection for umbrella releases.
These are selected documentation checks, not tested BEAML integration or evidence of a deployed distributed example.

**[Proposal]** The [distributed order probe](../planning/distributed-order-probe.md) narrows this target to three applications and one synthetic order.
The owner has not adopted its exact application split, protocol, storage, error cases or implementation plan.

**[Requirement]** The owner later requested precise planning and discussion before implementation.
A [separate capture](../../raw/requirements/2026-11-05-http-probe-plan.md) retains that instruction and selected component references.

**[Requirement]** The owner subsequently authorized implementation through a fresh-context GPT-6.1 Sol Medium agent workflow.
The [new capture](../../raw/requirements/2026-11-05-implementation-workflow.md) supersedes the earlier planning-only restriction.
The [Codex skill](../../skills/implement-step/SKILL.md) records the adapted procedure.

**[Verified]** The [repaired EXPERIMENT 0002 run](../../experiments/0002-http-correlation/results/20261105T220545655633Z/result.json) passed H01–H05 for two loopback HTTP releases and a synthetic order.
This local evidence covers correlated spans and logs and the deliberate missing TRACE CONTEXT control.
The broader source requirement includes DOMAIN EVENTS, order analysis and REPLAY RUNS. These remain outside the [experiment scope](../../experiments/0002-http-correlation/README.md#limits).
