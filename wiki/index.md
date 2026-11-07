# BEAML knowledge index

Start with the [R&D register](planning/research-and-development.md) for executable experiments and their limits. The [specification knowledge coverage audit](planning/specification-knowledge-coverage.md) maps S01-S45 to mechanisms, sources and open decisions. Then read the [product contract](concepts/product-contract.md), [build-readiness plan](planning/build-readiness.md) or [what to build first](queries/what-to-build-first.md). A small experimental compiler now exists; no production compiler/runtime or measured security/performance result is claimed.

The [source registry](sources/README.md) identifies pins/provenance/coverage; [maintenance guidance](../AGENTS.md) defines claim labels and ingest/query/lint workflows. Upstream capability is not BEAML capability; original explanatory examples/probes are unexecuted unless a result explicitly says otherwise.

## Specification, planning and retained answers

- [R&D register](planning/research-and-development.md): experiment process, candidate domain ownership and retained evidence.
- [Offene Fragen / Decisions to be made](planning/decisions-to-be-made.md): open R&D choices, evidence and decision triggers.
- [Decision log](planning/decision-log.md): closed decisions with options, reason and trigger, in order.
- [Main-agent orchestration](sources/main-agent-orchestration.md): adopted global coordination rule, worker scope and discovery limits.
- [Test-first policy](sources/test-first-policy.md): adopted RED, user review and GREEN checkpoints and their scope.
- [Implementation workflow](../skills/implement-step/SKILL.md): fresh GPT-6.1 Sol Medium agents, two Ponytail proposals and independent verification.
- [HTTP correlation EXPERIMENT](../experiments/0002-http-correlation/README.md): two loopback releases, passed H01–H05 and repeatable run and query commands.
- [Source-linked replay EXPERIMENT](../experiments/0003-source-linked-replay/README.md): proposed function summary, exact source lookup and isolated Orders replay.
- [Roasting rounds](planning/roasting-rounds.md): scope challenge, proposed boundary invariant and pending decisions.
- [Product-benefit probe](planning/product-benefit-probe.md): proposed comparison of small functions, typed failures and automatic observations.
- [Distributed order probe](planning/distributed-order-probe.md): proposed REST-separated umbrella example, correlated search and bounded replay.
- [Distributed order requirement](sources/distributed-order-requirement.md): owner target and selected propagation/deployment evidence.
- [Roasting sources](sources/roasting-rounds.md): selected conversation capture and review-method provenance.
- [Syntax spike requirement](sources/syntax-spike-requirement.md): accepted experimental syntax, R&D request and adopted initial Elixir backend.
- [PL syntax sentiment research](sources/pl-syntax-sentiment-2026.md): captured 2026 research on loved and hated syntax features; researcher ranking, snippet-only numbers and blocked forums as limits.
- [BAML syntax reception](sources/baml-syntax-reception-2026.md): how BAML's syntax is received, its scorecard against the sentiment rows (11 aligned, 8 tension, 4 mixed), the BAML/BEAML name facts; thin forum evidence as limit.
- [Working glossary](../GLOSSARY.md): scoped terms, proposed owners and German aliases; no universal runtime model.
- [Candidate context map](planning/context-map.md): language/compilation, execution and Observatory models with explicit translation boundaries.
- [Local strategy-wiki source](sources/agentic-strategy-wiki.md): selected local glossary/context patterns and provenance; no imported business model or policy.
- [Engineering specification v0.5](sources/engineering-spec-v0.5.md): preserved PDF, all sections, local S01-S45 inventory, exact proposed gates and phase tables.
- [Product contract](concepts/product-contract.md): language/runtime/UI/security ownership and validation/trust boundaries.
- [Knowledge coverage](planning/specification-knowledge-coverage.md): honest subclaim depth audit across the full spec and compiler/VM research.
- [Specification gaps](planning/specification-gaps.md): unresolved semantics, inconsistencies and design questions.
- [Build readiness](planning/build-readiness.md): requirement/evidence/decision/probe dependencies and first validation slice.
- [What should BEAML build first?](queries/what-to-build-first.md): source-backed saved answer.

## Event flow, typed errors and replay

- [Current typed replay requirement R01](sources/typed-replay-requirement.md): later user target and its relationship to the historical PDF.
- [Broadway/Kafka sources](sources/broadway-kafka.md): pinned selected demand, failure acknowledgment, offsets and retained-log limits.
- [Event flows and backpressure](concepts/event-flows-and-backpressure.md): per-context flows, admission, ordering, failure and measured adoption gates.
- [Event-sourcing/replay sources](sources/event-sourcing-and-replay.md): state folds, deterministic workflow history and compiler reproducers.
- [Pinned replay source validation](sources/replay-source-validation.md): missing workflow identity, sink isolation, compatible commands and crash uncertainty.
- [Vertical integration](concepts/vertical-integration.md): owner goal, one language from source to typed production data.
- [MIGRATE STEP fates](concepts/migrate-fates.md): DL-125 FATE OPERATIONS `redact`, `quarantine`, `retire`, `map`; proposed semantics and open questions.
- [Syntax sentiment](concepts/syntax-sentiment.md): loved and hated themes, BEAML scorecard (20 aligned, 5 tension, 7 gap), open items D026 to D033, decided after the first example applications (DL-135).
- [Typed errors and replay](concepts/typed-errors-and-replay.md): compiler/runtime capture profiles, GROUND TRUTH, typed-invalid fixtures, completeness, isolated reproduction and per-context acceptance.

## Types and formal reasoning

- [Type-system primary sources](sources/type-system-foundations.md): theorem, inference, evidence, refinement/effect and typestate evidence/limits.
- [Type-system foundations](concepts/types/type-system-foundations.md): judgment/safety scope, nominal/structural compatibility, variance, ADT coverage and missing/null.
- [Inference and polymorphism](concepts/types/type-inference-and-polymorphism.md): unification/occurs checks/generalization/skolems, kinds and deferred GADT/HKT/type-family complexity.
- [Trait evidence/coherence](concepts/types/traits-evidence-and-coherence.md): dictionary elaboration, deterministic resolution, overlap/termination, associated equality and roles.
- [Refinements and effects](concepts/types/refinements-and-effects.md): interval/SMT VCs, counterexamples/UNKNOWN, runtime conversion, latent callback effects and handlers.
- [Typestate/schema witnesses](concepts/types/typestate-and-schema-witnesses.md): reification/specialization, schema identity and alias/ownership/state failure examples.

## Compiler implementations and shared tooling

- [Compiler/tooling overview](concepts/compiler-and-tooling.md): proposed semantic core, IR/source maps/LSP and smallest complete slice.
- [Compiler/tooling primary references](sources/compiler-tooling.md): Rowan/Salsa/rust-analyzer/rustc/LSP/backend/test interfaces.
- [GHC source ledger](sources/ghc-compiler.md) and [GHC walkthrough](concepts/compilers/ghc.md): pinned frontend/constraints/evidence/FC Core/Lint/STG/Cmm/lazy runtime, with BEAML differences.
- [rustc source ledger](sources/rustc-internals.md) and [rustc walkthrough](concepts/compilers/rustc.md): expansion/hygiene/HIR/body goals/THIR/MIR/borrow/const/monomorphization.
- [BAML internals ledger](sources/baml-internals.md) and [BAML compiler/runtime walkthrough](concepts/compilers/baml.md): actual pinned parser/type/MIR/emitter/schema/stream/heap source; corrections to stale prose.
- [Incrementality and source identity](concepts/compilers/incremental-compilation-and-source-identity.md): red-green queries, source-span firewall, persistent/artifact IDs and fresh-equivalence tests.

## BAML product concepts and reuse

- [Established BAML docs](sources/baml-documentation.md): mutable BAML v0 (legacy DSL)/provider/SDK documentation track.
- [BAML v1](sources/baml-v1.md): general-purpose v1 language, stdlib, runtime, hosts, tooling, observability and 0.x beta status at pin `989676dd`.
- [Pinned BAML canary overview](sources/baml-canary-compiler.md): broader language/type/compiler track, linked to actual implementation detail.
- [BAML licensing](sources/baml-license.md): pinned root license and scoped reuse obligations.
- [BAML language/tooling](concepts/baml-language-and-tooling.md): inspiration versus compatibility decisions.
- [Structured output/streaming](concepts/structured-output-and-streaming.md): parser repairs, ordered preference, partial/final/default distinctions, revisions and retries.

## BEAM VM, OTP and typed boundaries

- [BEAM/OTP/Phoenix overview sources](sources/beam-otp-phoenix.md): earlier selected docs and version limits.
- [BEAM VM source ledger](sources/beam-vm-internals.md): pinned current OTP source and stale-guide caveats.
- [Typed BEAM precedents](sources/typed-beam-languages.md): Dialyzer, Gleam and current Elixir mechanisms.
- [Runtime/interop overview](concepts/beam-runtime-and-interop.md): generated API, Mix lifecycle, atom safety, tasks/cancellation and upgrades.
- [Execution and compilation](concepts/beam/execution-and-compilation.md): current Core→SSA, validator, register/root/tail-call, container/loader/JIT contracts.
- [Terms, memory and GC](concepts/beam/terms-memory-and-gc.md): tagged terms, maps, roots/copying, binary retention and streaming lifetime.
- [Processes/messages/OTP](concepts/beam/processes-messages-and-otp.md): delivery versus receive, priority queues/aliases, links/monitors, cancellation and restart semantics.
- [Scheduling/native/I/O](concepts/beam/scheduling-and-native-boundaries.md): reductions, dirty NIF limits, ports, readiness and bounded demand.
- [Distribution/storage/upgrades](concepts/beam/distribution-storage-and-upgrades.md): ETS races, descriptor lifetime, uncertain remote effects and schema/code version skew.
- [Inspection/performance](concepts/beam/inspection-and-performance.md): sensitive inspection/dumps, tools, measurement/control workloads and clock limits.
- [Typed-language boundaries](concepts/beam/typed-language-boundaries.md): static checks versus runtime validation, ordinary terms and witness/foreign trust.

## Phoenix and UI contracts

- [Phoenix/HEEx overview](concepts/phoenix-heex-integration.md): ownership, lifecycle and minimal seam.
- [Pinned UI mechanism sources](sources/phoenix-heex-mechanisms.md): parser/compiler/tokenizer/declarative/client/server/form adapter evidence.
- [HEEx analysis](concepts/ui/heex-analysis.md): passive parser hazards, structural facts/slots/assigns, byte/codepoint/UTF16 maps and rename transactions.
- [Typed forms/events](concepts/ui/typed-forms-and-events.md): transport normalization, draft versus validated state, descriptors and invalid-input zero-effects fixture.

## Domain models, architecture and evolution

- [Domain/contract/evolution sources](sources/domain-contracts-and-evolution.md): Evans/Eiffel/Ecto/Postgres/Akka/Avro/Protobuf/ArchUnit reference boundaries.
- [Domain modeling/contracts](concepts/domain-modeling-and-contracts.md): pure pre/postcondition/invariant obligations versus persistence, concurrent versions, external effects and recovery.
- [Schema/API evolution](concepts/schema-and-api-evolution.md): directional writer/reader, source/ABI/refinement/effect/security compatibility and version-pair fixtures.
- [Architecture/evidence](concepts/static-architecture-and-evidence.md): dependency paths/cycles/selectors, effects versus taint, manifests/statuses and separate release waivers.

## Verification, generators and benchmarks

- [Verification/testing sources](sources/compiler-verification.md): pinned Proptest/compiler tests, fuzzing and statistics evidence.
- [Compiler verification](concepts/testing/compiler-verification.md): independent oracles, MIR invariants, goldens/differential/metamorphic/fuzz testing and release/percentile uncertainty.
- [Generators/stateful properties](concepts/testing/generators-and-stateful-properties.md): constructive/rejected generation, exhaustion, legal shrinking, model commands and reproducible concrete regressions.

## Security, Observatory and knowledge practice

- [Information-flow sources](sources/information-flow-security.md) and [security mechanisms](concepts/information-flow-security.md): lattice/pc/exceptions/TCB/authority/UNKNOWN and scoped evidence.
- [Observability/storage sources](sources/observability-platforms.md) and [Observatory/replay](concepts/observability-and-replay.md): typed signals, sampling/cardinality, bounded queues/protocol failures, durable audit, tenant access and consented deletion.
- [Karpathy LLM Wiki](sources/karpathy-llm-wiki.md): raw/wiki/index/log workflow inspiration.
- [Decision4 source](sources/decision4.md) and [decision-consequence lens](concepts/decision-consequences.md): attributed decision framework, not inherited agent policy.
- [Source registry](sources/README.md), [log](log.md), [repository overview](../README.md), [maintenance guidance](../AGENTS.md).
