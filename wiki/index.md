# BEAML knowledge index

Start with the [product contract](concepts/product-contract.md), then [what to build first](queries/what-to-build-first.md) and the [build-readiness map](planning/build-readiness.md). The repository contains research and proposed design, not a working compiler/runtime. Claim labels distinguish requirements, verified upstream facts, proposals, inferences and unknowns; see [maintenance guidance](../AGENTS.md).

## Sources

- [Source registry](sources/README.md): versions, provenance, coverage and limits across the evidence set.
- [Engineering specification v0.5](sources/engineering-spec-v0.5.md): full PDF provenance, section requirement inventory, exact acceptance targets and phased gates.
- [Karpathy LLM Wiki](sources/karpathy-llm-wiki.md): raw/wiki/index/log workflow inspiration.
- [Decision4](sources/decision4.md): attributed consequence framework; research source, not inherited policy.
- [BAML established documentation](sources/baml-documentation.md): prompt/schema/provider/SDK concepts.
- [BAML canary compiler](sources/baml-canary-compiler.md): pinned broader language/compiler/runtime evidence.
- [BAML licensing](sources/baml-license.md): reuse boundaries at the pinned source revision.
- [Compiler and tooling sources](sources/compiler-tooling.md): lossless syntax, queries, IR, LSP and property-test precedents.
- [BEAM, OTP and Phoenix sources](sources/beam-otp-phoenix.md): Mix/runtime/HEEx boundary evidence.
- [Information-flow sources](sources/information-flow-security.md): labels, pc, authority and runtime threats.
- [Observability and storage sources](sources/observability-platforms.md): OTel privacy/context/queues, tenant isolation and retention limits.

## Concepts

- [Product contract](concepts/product-contract.md): language/compiler/runtime/UI/security ownership and trust boundaries.
- [BAML language and tooling](concepts/baml-language-and-tooling.md): inspiration and compatibility decisions.
- [Structured output and streaming](concepts/structured-output-and-streaming.md): partial/final validation, parser repairs, revisions and retry questions.
- [Compiler and tooling](concepts/compiler-and-tooling.md): semantic core, identities, invalidation, source maps and first slice.
- [BEAM runtime and interop](concepts/beam-runtime-and-interop.md): guarded ABI, atom safety, tasks, cancellation and upgrades.
- [Phoenix/HEEx integration](concepts/phoenix-heex-integration.md): official parser limits, typed forms/events, source mapping and lifecycle.
- [Information-flow security](concepts/information-flow-security.md): label algebra, pc, foreign UNKNOWN, explicit release and TCB.
- [Observatory and replay](concepts/observability-and-replay.md): safe metadata, context, bounded failure, storage and consented fixtures.
- [Decision consequences](concepts/decision-consequences.md): proposed way to document alternatives and commitments.

## Planning and saved answers

- [Specification gaps](planning/specification-gaps.md): explicit open decisions, inconsistencies and research questions.
- [Build readiness](planning/build-readiness.md): requirement-to-evidence-to-decision/probe map and proposed dependency order.
- [What should BEAML build first?](queries/what-to-build-first.md): concise source-backed answer, reusable in implementation planning.

## Operations

- [Maintenance guidance](../AGENTS.md): ingest, query and lint workflows; preserve raw inputs and source disagreements.
- [Log](log.md): append-only evidence/change history.
- [Repository overview](../README.md): local use, layout and source boundaries.
