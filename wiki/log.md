# Knowledge log

## [2026-11-05] setup | BEAML local knowledge base

Initialized an independent local Git repository on `main`, with no remote. Created the plain-Markdown layout, claim conventions, ingest/query/lint guidance, index, and log. No compiler/runtime implementation is claimed.

## [2026-11-05] ingest | Karpathy LLM Wiki

Read Andrej Karpathy's primary Gist body at revision `ac46de1ad27f92b28ac95459c782c07f6b8c964a`; saved a selected researcher capture and [source summary](sources/karpathy-llm-wiki.md). Full source text and comments were not copied. Adopted the raw/wiki/schema structure and index/log workflow as local conventions.

## [2026-11-05] ingest | Decision4 1.0.1

Captured selected unchanged upstream files at commit `5ccb19fc1fb8c6327d4edd8832550f7e8c40853e`, including both licenses and provenance. Added a [source summary](sources/decision4.md) and [proposed decision-documentation practice](concepts/decision-consequences.md). Decision4 remains an external research source; its agent contract is not automatically repository policy.

## [2026-11-05] ingest | BEAML engineering specification v0.5

Preserved the user-supplied 14-page PDF, SHA-256 provenance and full page-marked extraction under `raw/specification/`. Read all text and visually inspected representative appendix pages 8/12. Added [section inventory/exact gates](sources/engineering-spec-v0.5.md), [product contract](concepts/product-contract.md) and [gap queue](planning/specification-gaps.md). Recorded v0.3/v0.4/v0.5 composition, syntax/status drift, incomplete formal grammar and security rollout ambiguities. Document instructions treated as evidence, not agent commands.

## [2026-11-05] research | BAML and compiler/tooling

Added [established BAML docs](sources/baml-documentation.md), [pinned canary compiler](sources/baml-canary-compiler.md), [reuse/license boundary](sources/baml-license.md) and [compiler/tooling sources](sources/compiler-tooling.md), with dated selected raw/provenance records. Synthesized [language/tooling](concepts/baml-language-and-tooling.md), [structured output/streams](concepts/structured-output-and-streaming.md) and [compiler/tooling](concepts/compiler-and-tooling.md). Kept DSL/canary tracks distinct; no compatibility claim, copied implementation, dependency choice or prototype execution.

## [2026-11-05] research | BEAM, Mix and Phoenix

Captured selected primary docs and pinned LiveView parser-source evidence; added [source inventory](sources/beam-otp-phoenix.md), [runtime/interop](concepts/beam-runtime-and-interop.md) and [HEEx integration](concepts/phoenix-heex-integration.md). Recorded guarded ABI, atom safety, native/task cancellation limits, Mix stale/deleted outputs, internal parser support and source-span/lifecycle probes. No runtime integration executed.

## [2026-11-05] research | Information-flow and Observatory

Captured 14 attributed selected primary-evidence records plus capture hash under `raw/research/security-observability/`. Added [IFC sources](sources/information-flow-security.md), [platform sources](sources/observability-platforms.md), [security synthesis](concepts/information-flow-security.md) and [Observatory/replay synthesis](concepts/observability-and-replay.md). Distinguished source requirements from candidate lattice/interop/telemetry designs; noted pc/error channels, OTel signal maturity, baggage trust, disk queues and asynchronous/versioned retention. No proof audit, deployment or deletion experiment.

## [2026-11-05] synthesize | Build-readiness and navigation

Connected all evidence through the [source registry](sources/README.md), [build-readiness map](planning/build-readiness.md), saved [first-build answer](queries/what-to-build-first.md), updated index and repository overview. Proposed a grammar/ABI/semantic-identity/security decision sequence and small compiler-to-BEAM validation slice, then telemetry and Phoenix seams. Exact specification gate tables remain in the source inventory; proposed probe checks are labeled separately. Local provenance, page-count and owned-page link checks passed during ingestion; independent repository QA recorded separately after integration.

## [2026-11-05] lint | Independent structural and evidence spot check

`python3 scripts/lint_wiki.py --self-test` passed, including duplicate/Unicode heading anchors, fenced examples, missing targets/anchors, index/orphans, source metadata and absolute/traversal/symlink escape rejection. `python3 scripts/lint_wiki.py` checked 27 maintained Markdown files with zero errors; PDF SHA-256/bytes/14 pages and fresh per-page Poppler extraction matched. The retained PDF also matched the supplied original by hash. README commands match the checked script. Unchanged raw originals are exempt from internal link lint, while maintained links into raw evidence are checked.

Independent primary-source spot checks supported BAML assertion filtering and partial-stream controls, Jif pc/exception treatment, and OTel Erlang signal maturity. Decision4 attribution, unchanged-capture status and CC BY text/MIT schema distinction are recorded. Limits: inline Markdown/local heading checks, metadata presence and selected factual checks only; no complete source audit, external-link crawl, implementation execution, benchmark or security proof.

## [2026-11-05] deepen | Type mechanisms and GHC source trace

Expanded the requested knowledge depth with [type-system evidence](sources/type-system-foundations.md), five mechanism guides under `concepts/types/`, and [GHC source](sources/ghc-compiler.md)/[walkthrough](concepts/compilers/ghc.md). Original unexecuted examples explain progress/preservation scope, unification/generalization/rigid checking, nominal/structural variance, ADT coverage, trait dictionaries/coherence/associated equality, refinement VC/UNKNOWN, latent effects/handlers, Schema witnesses and typestate alias limits. GHC9.12.2 release tag was resolved later to mirror commit `383be28ffdddf65b57b7b111bfc89808b4229ebc` in a new immutable supplement; Tc.Module evidence confirms simplifyTop→error stop→zonk ordering. Selected Core/Lint/STG/Cmm/runtime references do not imply complete compiler/theorem audit or a build.

## [2026-11-05] deepen | Compiler, VM, testing and UI mechanisms

Added pinned [rustc](sources/rustc-internals.md), [BAML internals](sources/baml-internals.md), [BEAM VM](sources/beam-vm-internals.md), [typed BEAM](sources/typed-beam-languages.md), [verification/generation](sources/compiler-verification.md) and [Phoenix/HEEx](sources/phoenix-heex-mechanisms.md) evidence plus connected mechanism walkthroughs. Topics include expansion/hygiene/constraint evidence, typed IR/verifier boundaries, incremental identity/source maps, operational generation/shrinking/exhaustion, current VM compiler/loader/JIT/GC/process/scheduler/native/distribution/upgrade semantics, and actual HEEx/form/slot/source-edit boundaries. Benchmark analysis distinguishes mean and percentile uncertainty and the limits of thirty runs for p99. Inspected upstream fixtures remain assertions, not reported executed passes.

## [2026-11-05] correct | Source prose and version-track drift

Kept historical raw inputs unchanged and corrected maintained BAML summaries using actual pinned source: conceptual TIR is implemented in `baml_compiler2_hir_ty`; BexEngine uses heap permits/parking/root relocation rather than the stale README epoch description; established SDK partial types/syntax are distinct from pinned canary shared-T partial defaults/colon/backtick syntax. [Corrected walkthrough](concepts/compilers/baml.md). Current OTP source lowers Core directly into SSA through an integrated converter; historical Kernel pass naming is not a separate present IR, and binary-layout guide prose has acknowledged historical limits. [Compiler](concepts/beam/execution-and-compilation.md), [memory](concepts/beam/terms-memory-and-gc.md). These corrections supersede earlier derived interpretations; raw captures preserve how the evidence was encountered.

## [2026-11-05] deepen | Security and operational Observatory

Expanded [IFC](concepts/information-flow-security.md) with candidate policy algebra/correlation pitfalls, pc/exception observations, concrete TCB and authority/UNKNOWN evidence. Expanded [Observatory](concepts/observability-and-replay.md) with typed signal mapping, sampling versus recording, cardinality/queue calculations, OTLP partial acceptance, durable-audit crash windows and tenant/consent/versioned-erasure operations. New immutable selected-evidence supplement records exact OTel/OTLP/W3C/Postgres/source versions. Proposed policies/calculations are unexecuted; transport acceptance, queue persistence and GET404 do not establish end-to-end durability or erasure.

## [2026-11-05] deepen | Domain, evolution and architecture consequences

Added [primary domain/evolution evidence](sources/domain-contracts-and-evolution.md) and local [domain-transition](concepts/domain-modeling-and-contracts.md), [schema/API compatibility](concepts/schema-and-api-evolution.md), and [architecture/evidence](concepts/static-architecture-and-evidence.md) mechanisms. Worked cases distinguish pure invariant preservation from transaction/external delivery, directional wire compatibility from domain/effect/security meaning, graph reachability/cycles from effect and taint analysis, and claim status from release waivers. These source-backed alternatives remain unadopted/unexecuted BEAML design.

## [2026-11-05] audit | All-spec knowledge coverage and peer review

Created the [knowledge coverage audit](planning/specification-knowledge-coverage.md), covering every S01-S45 group with bundled subclaims separated and explicit GHC/Rust/BAML/BEAM reading tracks. Audited delivered local mechanisms before upgrading depth; all initially pending parser/testing/UI/domain/architecture/statistics reference topics now have explanatory pages and primary evidence. Remaining unselected semantics, selected-source/proof-review limitations and absent executable validation remain explicit. Index/registry/README route to the expanded depth and historical-correction notes. Independent peer review confirmed selected type/GHC/IFC/OTel/BEAM claim scope; corrected the illustrative GHC failure to use an annotated Int literal so its stated mismatch cannot be explained instead by numeric overloading. Validator self-test and full run passed at60 maintained Markdown files, no errors, with PDF hash/bytes/page/per-page extraction and three retained-capture hashes checked. Independent final QA follows in a separate entry.

## [2026-11-05] followup | GHC solver and demand analysis

Closed the central source-access gap with account-scoped official-mirror reads at the existing GHC commit. Preserved a new [selected supplement/provenance](../raw/research/type-systems-ghc/2026-11-05-solver-demand-followup.md) covering seven actual Solver/Solve/Dict/Equality/DmdAnal/WorkWrap files. Expanded [GHC mechanisms](concepts/compilers/ghc.md) with worklist/canonical/inert reprocessing, controlled unification and evidence construction, nested implication scope, LetUp/LetDown demand and recursive fallback, boxity-to-worker-wrapper calling-convention invariants. Added inference/trait cross-links and updated coverage to supersede earlier fetch failures while retaining selected-section/theorem-audit/execution limits. No GHC build or BEAML probe was run.

## [2026-11-05] audit | Independent final depth review

Independent review found no blocking issue in the expanded source-status boundaries, domain/evolution/architecture mechanisms or all-spec coverage mapping. Selected primary checks supported GHC Core Lint's conditional guarantee and typechecker ordering, IFC policy/exception scope and OTLP partial-success/nonblocking-hook limits. The final validator self-test and full run passed: 60 maintained Markdown files, zero errors, original PDF hash/bytes/14 pages/per-page text and four explicitly retained capture hashes checked. Previously committed raw inputs remain unchanged; changed-file whitespace checks passed. Validation remains selected source inspection and local structural/provenance checks: no external-link crawl, exhaustive semantic/theorem audit, runtime implementation, compiler execution, benchmark or security proof.

## [2026-11-05] publish | Public repository and license

**[Requirement]** The repository owner requested publication of the tracked knowledge base, including the supplied specification. The owner selected Apache License 2.0. **[Verified]** Created the public [13ue/beaml repository](https://github.com/13ue/beaml). Updated the [repository overview](../README.md) and added the [license](../LICENSE). Third-party captures retain their existing terms. Raw evidence remains unchanged.

## [2026-11-05] propose | Shared glossary and candidate contexts

Created the [working glossary](../GLOSSARY.md) before the [context-map proposal](planning/context-map.md). Three candidate models preserve one compiler semantic authority and separate runtime outcomes from observations. Agent roles stay provisional. Foreign provider, host, UI and OTel models have explicit translation seams. The [local source note](sources/agentic-strategy-wiki.md) records selected secondary patterns with original paraphrases and source hashes; unrelated business models and source instructions were not imported. DOMAIN EVENT does not imply committed publication. OBSERVATORY can have authorized administration without redefining source or business facts. No implementation, new dependency, complete controlled grammar or certification is claimed.

Independent review clarified SCHEMA WITNESS versus authority and limited ANTI-CORRUPTION LAYERS to real model differences. Full local lint passed at 62 maintained files, zero errors, PDF checks and five retained-capture hashes. A targeted check reused the validator helpers for the root glossary: four links/anchors, index entry and 30 unique terms passed. The script was unchanged; root glossary checks are manual additions to this run. No external-link crawl, full local-source audit or runtime experiment was performed.

## 2026-11-05 — Event flows and central typed replay requirement

**[Requirement]** Retained a selective dated user request R01 for Broadway/Kafka flow mapping and fully typed surrounding execution replay on error. Historical PDF/raw evidence remains unchanged. The new target expands earlier fixture-only scope; no unrestricted capture, secret access or framework adoption is inferred.

**[Verified]** Added selected Broadway 1.3.0, BroadwayKafka 0.7.1, GenStage 1.3.2 and Kafka 4.4 evidence. Source inspection exposed always-ack failed-message behavior in the standard Kafka connector, a material gate for required durable retry/capture. Added selected Temporal/Akka/Clang mechanisms and pinned Temporal TypeScript SDK source. The history format omits workflow identity; optional replay sinks need isolation; ordinary activity history omits full intermediate retries. No engine or pipeline was executed.

**[Proposal]** Added glossary terms before use. Added per-context flow/backpressure design, a typed error algebra, compiler and execution REPLAY CAPSULE profiles, scoped GROUND TRUTH, invalid-input fixtures, separate durable capture admission, crash/unknown-outcome handling and an isolated REPLAY RUN. Original-error reproduction, runner success and CAPTURE COMPLETENESS are separate results. Added per-context acceptance checks and full-target design/validation gaps; reconciled Observatory/domain/build-readiness/coverage and navigation. No implementation result is claimed.

Peer review checked typed replay against source boundaries and reviewed the connector failure gate. Structural validation results follow after stable-file integration; link/provenance checks do not establish behavior.

## [2026-11-05] audit | Event flows and typed replay

Independent review checked acknowledgement failure windows, originating-context ownership, candidate error outcomes and the three replay result axes. Pinned SDK source confirmed separate workflow identity and replay sink opt-in behavior. The Broadway failure-callback contract and Kafka acknowledger support the stated adapter-selection gate. No blocking issue remained after the error-ownership correction. Self-tests and full lint passed: 68 maintained pages, zero errors, PDF integrity/extraction and six retained-capture hashes. The root glossary passed separate link, anchor, index and uniqueness checks for 41 terms. Previously committed raw evidence remains unchanged; whitespace checks passed. Scripts stayed unchanged. Limits remain local structural checks and selected primary-source inspection. No broker fault test, replay runner, capture-completeness proof, semantic audit or benchmark was executed.

## [2026-11-05] experiment | R&D repository and syntax-to-BEAM probe

**[Requirement]** The owner selected exact data interfaces, partial record patterns without `..`, unparenthesized function definitions and parenthesized calls/constructors. The owner requested an R&D repository and recorded experiments. [Source and selected capture](sources/syntax-spike-requirement.md). Added the [R&D register](planning/research-and-development.md), EXPERIMENT terms, repository guidance and the first [experiment package](../experiments/0001-syntax-to-beam/README.md). Candidate owners are LANGUAGE/COMPILATION and EXECUTION. This does not adopt separate services or a complete architecture.

**[Verified]** [EXPERIMENT RUN 20261105T202319485083Z](../experiments/0001-syntax-to-beam/results/20261105T202319485083Z/result.json) passed with Rust/Cargo 1.94.0, Elixir 1.18.1 and OTP 27. Rust formatting and Clippy passed. Nine compiler unit tests, one CLI integration test and eight BEAM tests passed. The coverage test checks all sixteen subsets of a four-value truth table. Generated Elixir compiled to BEAM with warnings treated as errors. The tests exercise exact structural interfaces, nested ordered patterns, constructor/function arity, exhaustive clauses, invalid host values and strings kept as data. Retained text artifacts, tool versions and SHA-256 hashes identify the tested inputs and generated outputs. An earlier generator failure remains recorded. Local action events omit source text and input paths.

Updated README, index, compiler guidance, build readiness, gap notes, coverage audit and the earlier first-build answer. These pages now separate this smaller executed probe from the broader unimplemented plan. **[Unknown]** Generics, recursive TYPEs, method interfaces, effects, LSP, providers, full typed replay and production guarantees remain absent. M0 and M3 are not complete. The result is local experimental evidence, not a security or performance proof.

## [2026-11-05] decision | Initial Elixir backend

**[Requirement]** The owner adopted BEAML → generated Elixir source → Elixir/OTP compiler → BEAM execution as the initial route. A [new capture](../raw/requirements/2026-11-05-elixir-backend-decision.md) preserves the decision. Updated the [source note](sources/syntax-spike-requirement.md), [compiler guidance](concepts/compiler-and-tooling.md), [build plan](planning/build-readiness.md), [R&D register](planning/research-and-development.md) and index. Direct BEAM assembly or bytecode emission is not an adopted later goal. **[Unknown]** Permanent backend selection and comparative performance remain open. No compiler code changed or new runtime test was required.
