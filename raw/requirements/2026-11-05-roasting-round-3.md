---
id: raw-roasting-round-3-2026-11-05
kind: selected-conversation-and-research-capture
date: 2026-11-05
---

# Review the competitive claim (round 3)

Origin: repository-owner conversation and the AUTHORING AGENT's spec-mode review on 2026-11-05.
This is a selected paraphrase and source record. It omits the full conversation and copies no third-party prose.
The repository review convention requires retention. The [review record](../../wiki/planning/roasting-rounds.md#round-3--test-the-competitive-claim-2026-11-05) contains the full objection dispositions.
The [earlier capture](2026-11-05-roasting-rounds.md) retains rounds 1 and 2.

## Owner position and review target

**[Requirement]** Challenge BEAML's current state and proposed next proof in a direct Devil's Advocate review.
**[Verified]** The owner states an ambition to compete with BAML, be approximately 3–8× better including scope, and gain a large advantage from BEAM and Elixir.
The review treats that as a claim to test. The owner did not supply a denominator or adopt the review's test gates.

**[Verified]** [EXPERIMENT 0001](../../experiments/0001-syntax-to-beam/README.md#evidence-and-limits) ran its bounded compiler and BEAM tests.
[EXPERIMENT 0002](../../experiments/0002-http-correlation/workflow/2026-11-05/result.json) passed its independent final checks, including the [H01–H05 run](../../experiments/0002-http-correlation/results/20261105T221134010042Z/result.json).
Host instrumentation surrounds generated fixture functions. The payment endpoint has a fixed synthetic response and performs no business mutation.
The proposed [Orders-only REPLAY RUN](../../wiki/planning/distributed-order-probe.md#replay-is-more-than-a-joined-search-result) has no executed result.

## BAML evidence

Publisher: BoundaryML. Access date: 2026-11-05.
Documentation and source observations have their upstream terms and licenses. See the [BAML license source](../../wiki/sources/baml-license.md).
No competitor build or benchmark ran. No feature parity or absence claim is made for composed, isolated cross-service replay.

**[Verified]** The established BAML v0 [changelog](https://docs.boundaryml.com/changelog/changelog#02263---2026-10-27) lists 0.226.3 on 2026-10-27.
The mutable v0 docs describe [typed generated clients and structured parsing](https://docs.boundaryml.com/guide/introduction/what-is-baml),
[structured partial streaming](https://docs.boundaryml.com/guide/baml-basics/streaming),
[retry](https://docs.boundaryml.com/ref/llm-client-strategies/retry-policy) and [fallback](https://docs.boundaryml.com/ref/llm-client-strategies/fallback),
[function tests](https://docs.boundaryml.com/ref/baml/test) and the [Collector's call and HTTP attempt data](https://docs.boundaryml.com/guide/baml-advanced/collector-track-tokens).
The [REST/OpenAPI guide](https://docs.boundaryml.com/guide/installation-language/rest-api-other-languages) calls the integration a preview.
The [Elixir guide](https://docs.boundaryml.com/guide/installation-language/elixir) describes the community integration as unstable.

**[Verified]** BoundaryML's newer [language book](https://developer.boundaryml.com/baml/book/errors) documents inferred typed errors.
Its [concurrency chapter](https://developer.boundaryml.com/baml/book/concurrency) shows named tasks, execution telemetry and SQL queries.
The [versioned CLI 0.22.1 reference](https://developer.boundaryml.com/cli/v0.22.1/commands/query) documents querying BTEL recordings.
The [GitHub releases listing](https://github.com/BoundaryML/baml/releases) showed the 0.23.1 nightly series.
The local [canary source note](../../wiki/sources/baml-canary-compiler.md) independently records a specific 2026-11-05 source pin and its release observations.
No claim is made that the documents describe one tested release or stable interface.

## Review outcome

**[Inference]** Scope does not give a value ratio. BAML has substantial overlap, and idiomatic Elixir already has OTP.
HTTP traces do not settle remote commitment. Fixture replay alone cannot establish a language advantage.
**[Proposal]** Test one compiler-derived boundary with equivalent host baselines, explicit replay controls and timed incident reproduction.
**[Unknown]** No head-to-head result, general claim of superiority or owner disposition was established in this review.
