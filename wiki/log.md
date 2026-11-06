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

## [2026-11-05] record | BEAML roasting rounds

**[Requirement]** The owner requested repository records of both roasting rounds.
Added a [selected conversation capture](../raw/requirements/2026-11-05-roasting-rounds.md), [source note](sources/roasting-rounds.md) and [review record](planning/roasting-rounds.md).
Round 1 uses the retained summary; its full wording and severity list remain unavailable.
Round 2 records the proposed boundary invariant, evidence gap and simulated-effect test.
Updated the index, source registry and R&D register. Human dispositions remain pending.
No new EXPERIMENT, compiler change or runtime test is claimed.

## [2026-11-05] rule | Retain every roasting round

**[Requirement]** The owner requires every BEAML roasting or Devil's Advocate round to be documented in the repository.
Added the rule to [AGENTS.md](../AGENTS.md#roasting-and-devils-advocate-rounds).
Each round needs a dated review entry, a separate capture, source-note maintenance and a log entry.
Keep evidence, proposals and actual owner decisions separate. Pending objections do not become accepted decisions.
The rule does not require automatic implementation, commits or pushes.

## [2026-11-05] clarify | Product benefit after roasting round 2

Recorded the correction: boundary validation alone cannot justify a separate language.
Preserved a [new conversation and research capture](../raw/requirements/2026-11-05-product-benefit-followup.md).
Checked official BAML Collector and error documentation; kept their version tracks and execution limits separate.
Updated the [BAML source](sources/baml-documentation.md), [review source](sources/roasting-rounds.md) and [round 2 follow-up](planning/roasting-rounds.md).
Added an unadopted [product-benefit probe](planning/product-benefit-probe.md), with a fair Elixir comparison and change test.
Updated the index and R&D register. No new compiler feature, EXPERIMENT RUN or performance claim exists.

## [2026-11-05] record | Distributed order product target

**[Requirement]** The owner requests REST-separated Elixir applications with correlated traces, logs, events, orders, analysis and replay.
Added a [selected capture](../raw/requirements/2026-11-05-distributed-order-observability.md) and [source note](sources/distributed-order-requirement.md).
Added a [three-application proposal](planning/distributed-order-probe.md), with order-level search, timeout uncertainty and scoped isolated replay.
Kept umbrella layout, network deployment, observed traces and committed facts distinct.
Updated the local product-benefit proposal, R&D register, Observatory concept, source registry and index.
The exact probe is unadopted and unexecuted. No new compiler, distributed runtime or replay result is claimed.

## [2026-11-05] plan | Two-application HTTP correlation

**[Requirement]** The owner requested an exact plan and discussion before implementation.
Preserved the [planning request](../raw/requirements/2026-11-05-http-probe-plan.md).
Added [EXPERIMENT 0002's proposed plan](../experiments/0002-http-correlation/README.md), with two independent processes, compiled BEAML fixtures, real OTel spans and correlated structured logs.
Defined HTTP shapes, six spans, five acceptance cases, file evidence, query behavior, implementation sequence and limits.
Added a plan-only registry entry and index link. Updated the broader distributed proposal and its source note.
No dependencies were installed, no compiler code changed and no runtime test was executed. Replay remains a separate later proposal.

## [2026-11-05] adopt | Fresh-context implementation workflow

**[Requirement]** The owner requested the Claude workflow adaptation and its use for EXPERIMENT 0002.
All phase agents use GPT-6.1 Sol Medium with fresh contexts. [Adoption capture](../raw/requirements/2026-11-05-implementation-workflow.md).
Added the [versioned skill](../skills/implement-step/SKILL.md), installed its global copy and passed skill validation.
The workflow retains planning, competing Ponytail proposals, implementation decisions, tests, review and final verification.
Updated AGENTS.md, source note, index and the experiment's authorization state. Implementation results follow separately.

## [2026-11-05] adopt | Global main-agent coordination

**[Requirement]** The owner requires the user-facing main agent to coordinate fresh workers for every task.
Workers perform all substantive work, including reads, records, documentation, configuration, tests and final diff inspection.
Preserved existing global rules and appended the coordination policy to the default global `AGENTS.md`.
Updated the [project rule](../AGENTS.md#main-agent-coordination) and both repository/installed [workflow skill](../skills/implement-step/SKILL.md) copies.
Removed task-specific authorization from project rules; its [existing capture](../raw/requirements/2026-11-05-implementation-workflow.md) remains unchanged.
Retained a [new adoption capture](../raw/requirements/2026-11-05-global-main-agent-orchestration.md) and indexed its [source note](sources/main-agent-orchestration.md).
**[Verified]** Official instruction-discovery documentation confirms default global override precedence and loading at run start.
No global or repository-root override file exists. Both skill copies and their UI metadata agree.
Both bundled skill validations passed. Wiki checks passed: 76 maintained Markdown files, zero errors, six retained capture hashes.
Limits: these files guide future runs; no live reload, enforced compliance or EXPERIMENT result is claimed.
No review round, automatic commit or push was performed.

## [2026-11-05] clarify | Event-driven main-agent coordination

**[Requirement]** The owner rejects repeated short waits and polling by the user-facing main agent.
Preserved the [clarification](../raw/requirements/2026-11-05-global-main-agent-orchestration-v2.md) in a new immutable capture.
Updated global and project rules, both implementation skill copies and the [source note](sources/main-agent-orchestration.md).
Workers send milestone, blocker and completion notifications. The main agent yields when nothing is actionable.
The main agent must not sleep, poll, read status repeatedly or block on tool waits.
Workers may use bounded subprocess lifecycle checks for assigned work.
**[Verified]** Both skill validations passed again. Skill/UI copies agree; default global/project override checks passed.
Limits: no future compliance proof, live reload, EXPERIMENT result, commit or push is claimed.

## [2026-11-05] adopt | Test-first policy

**[Requirement]** The owner adopted meaningful RED, user review and GREEN for behavior changes.
The [adoption capture](../raw/requirements/2026-11-05-test-first-policy.md) records the checkpoint, exceptions and scope.
Indexed the [test-first policy source](sources/test-first-policy.md) and added it to the [source registry](sources/README.md).
The adoption defines an instruction. Runtime enforcement remains outside its scope.

## [2026-11-05] record | HTTP correlation run

**[Verified]** The [repaired EXPERIMENT RUN](../experiments/0002-http-correlation/results/20261105T220545655633Z/result.json) passed H01–H05.
H03 preserved two traces, four local edges and two logs. It reported only the missing cross-service parent edge.
The [repair log](../experiments/0002-http-correlation/workflow/2026-11-05/repair-green.log) records the focused checks.
The [forced failure run](../experiments/0002-http-correlation/results/20261105T220612131147Z/result.json) records clean exits after a deliberate failure.
Updated the [experiment guide](../experiments/0002-http-correlation/README.md), [R&D register](planning/research-and-development.md), index and distributed order and Observatory notes.
Independent final verification remains pending. The result covers fixed loopback correlation. REPLAY RUNS and production readiness remain outside scope.

## [2026-11-05] verify | HTTP correlation EXPERIMENT

**[Verified]** [Independent final verification](../experiments/0002-http-correlation/workflow/2026-11-05/result.json) passed all seven repair assertions.
The [final EXPERIMENT RUN](../experiments/0002-http-correlation/results/20261105T221134010042Z/result.json) passed H01–H05.
The owner adopted the review checkpoint after the initial GREEN. Owner review of the initial RED remains unverified. The owner approved the seven repair assertions before implementation.
Updated the [experiment guide](../experiments/0002-http-correlation/README.md) and [R&D register](planning/research-and-development.md).
The result covers fixed loopback correlation and bounded local observations. REPLAY RUNS and production readiness remain outside scope.

## [2026-11-05] adopt | Visual communication

**[Requirement]** The owner requested visuals by default for substantive explanations and reports in Codex and BEAML.
The [BEAML rule](../AGENTS.md#visual-communication) covers ownership, tested flow, results, limits and the next test.

## [2026-11-05] review | BEAML competitive claim

**[Inference]** [Round 3](planning/roasting-rounds.md#round-3--test-the-competitive-claim-2026-11-05) questions the 3–8× measure, the BAML comparison and the value of fixture replay.
The [new capture](../raw/requirements/2026-11-05-roasting-round-3.md) and [source note](sources/roasting-rounds.md#round-3--competitive-claim) record evidence and limits.
The proposed comparison remains pending. No new runtime results or owner decisions were recorded.

## [2026-11-05] record | Open R&D decisions

**[Requirement]** The owner requested a durable register for open R&D decisions.
[D001](planning/decisions-to-be-made.md#d001--enum-or-type-declarations) records the `enum` or `type` question as OPEN.
The [selected capture](../raw/requirements/2026-11-05-enum-or-type.md) records the request.
Linked the register from the index, R&D guidance and [EXPERIMENT 0001](../experiments/0001-syntax-to-beam/README.md).
The declaration examples and next grammar check are proposals. The owner has yet to choose a form.

## [2026-11-05] plan | Source-linked Orders replay

**[Proposal]** Added the [EXPERIMENT 0003 plan](../experiments/0003-source-linked-replay/README.md) to the [R&D register](planning/research-and-development.md) and index.
It extends the two-release loopback case with one function summary, a same-name revision control and one isolated REPLAY RUN.
The plan is pending review and has no runtime results.

## [2026-11-05] record | Ecto and LiveView candidate

**[Requirement]** The owner requested a later Ecto and LiveView integration slice and prioritized HTTP trace, source lookup and replay in EXPERIMENT 0003.
**[Proposal]** The [R&D candidate](planning/research-and-development.md#later-candidate--ecto-and-liveview) records the explicit mapping, host boundaries and tests for rejection, outer commit and missing evidence.
The follow-up order is open. The candidate has no runtime results.

## [2026-11-06] verify | EXPERIMENT 0003 lookup gate

**[Verified]** The independent TEST and review of the lookup repair passed. The fresh live run and the repair run with `--source-run` exited 0. The review found no defect. [TEST record](../experiments/0003-source-linked-replay/workflow/2026-11-05/lookup/repair-test-result.json), [review](../experiments/0003-source-linked-replay/workflow/2026-11-05/lookup/repair-review.md)
**[Requirement]** The owner chose option B. Always run the repair test with `--source-run <fresh live result dir>`. The test default and the retained `missing_clock` archive stay unchanged. Fresh Claude Opus 5.5 workers ran this gate by owner choice.
Updated the [lookup notes](../experiments/0003-source-linked-replay/workflow/2026-11-05/lookup/notes.md#lookup-repair-test-review-and-owner-decision), the workflow record, the [EXPERIMENT 0003 page](../experiments/0003-source-linked-replay/README.md#gate-status) and the [R&D register](planning/research-and-development.md#experiment-register).
**[Unknown]** CAPTURE, transport observation and REPLAY RUN have no run. `run.py` does not exist yet. Partial windows were checked only in scratch derivatives.

## [2026-11-06] verify | EXPERIMENT 0003 CAPTURE gate

**[Verified]** The CAPTURE and transport observer gate passed. The owner reviewed the RED and chose one response record per live receipt. GREEN added 22 lines to `OrdersApi.PaymentHttp`. The independent TEST passed 10 of 10 checks. The review passed with four non-blocking advisories. [Notes](../experiments/0003-source-linked-replay/workflow/2026-11-05/capture/notes.md), [TEST record](../experiments/0003-source-linked-replay/workflow/2026-11-05/capture/test-result.json), [review](../experiments/0003-source-linked-replay/workflow/2026-11-05/capture/review.md)
**[Verified]** No test is lost. GREEN ran `test_query.py` with 6 tests. `unittest discover` runs 8 tests: `test_query.py` 6 and `test_runner.py` 2. Fresh Claude Opus 5.5 workers ran this gate by owner choice.
Updated the workflow record, the [EXPERIMENT 0003 page](../experiments/0003-source-linked-replay/README.md#gate-status) and the [R&D register](planning/research-and-development.md#experiment-register).
**[Unknown]** The test cannot show raw bytes with a compact body (A1). The Orders artifact ID does not cover the host decode and validation (A3). The owner decides A1 and A3. REPLAY RUN and invalid replay records have no run. `run.py` does not exist yet.

## [2026-11-06] decide | EXPERIMENT 0003 review advisories

**[Requirement]** The owner decided the CAPTURE review advisories. A1 goes into the gate 4 RED with a non-canonical body. A3 stays open as [D002](planning/decisions-to-be-made.md#d002--scope-of-the-replay-artifact-identity). The response record gets no timestamp for data economy. The time comes from the trace span.
**[Inference]** Trace sampling can remove that time. [D003](planning/decisions-to-be-made.md#d003--trace-sampling-and-retained-response-records) records this as OPEN.
Updated the [EXPERIMENT 0003 page](../experiments/0003-source-linked-replay/README.md#evidence-and-limits) and the [CAPTURE notes](../experiments/0003-source-linked-replay/workflow/2026-11-05/capture/notes.md#owner-decisions-after-review).

## [2026-11-06] ingest | BAML debugging and replay

**[Verified]** Read BAML v0 docs (Collector, modular API, Boundary Studio, test blocks, `baml-cli test`) and v1 code at `canary` `6a3eb3dfb2908bac750ad0e4cd9d6a086a72f211`. The read files match the pin `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`. [Capture](../raw/research/baml/debugging-replay-2026-11-06.md)
**[Verified]** BAML records raw HTTP responses and re-parses reply text offline (`b.parse`, `F@parse`). No built-in replay runner was found. Playground HTTP replay is open pull request #3336, not merged.
**[Inference]** BAML offers introspection and offline re-parse, not a REPLAY RUN with isolation and evidence checks.
Updated [BAML docs](sources/baml-documentation.md#debugging-and-replay-of-a-recorded-call-2026-11-06), [BAML internals](sources/baml-internals.md#recorded-calls-and-offline-parse-2026-11-06) and the [Observatory comparison](concepts/observability-and-replay.md#baml-recorded-call-debugging-compared-with-experiment-0003).
**[Unknown]** Nothing was run. Body-recording defaults, byte fidelity and code-search completeness are not established. The EXPERIMENT 0003 page is unchanged; its replay decision is open elsewhere.

## [2026-11-06] verify | EXPERIMENT 0003 REPLAY RUN gate

**[Verified]** Gate 4 passed (acceptance cases 4 and 5). RED revision 3 had an agent RED review and a fresh check. GREEN added `OrdersApi.Replay.run/3` and one shared `PaymentHttp.decode/1`. The REPLAY RUN had zero transport entries. Six invalid records failed with typed reasons before decode. [Notes](../experiments/0003-source-linked-replay/workflow/2026-11-05/replay/notes.md), [GREEN run](../experiments/0003-source-linked-replay/results/20261106T080316413341Z/result.json)
**[Verified]** The independent TEST passed 9 of 10 checks. `git diff --check` failed only on blank lines in retained raw run logs; the main agent accepted this. The final review gave PASS WITH CHANGES. [TEST record](../experiments/0003-source-linked-replay/workflow/2026-11-05/replay/test-result.json), [review](../experiments/0003-source-linked-replay/workflow/2026-11-05/replay/review.md)
Updated the workflow record, the [EXPERIMENT 0003 page](../experiments/0003-source-linked-replay/README.md#gate-status), its overview page and the [R&D register](planning/research-and-development.md#experiment-register).
**[Unknown]** The runner does not bind the record to the loaded build (R1, waits for [D002](planning/decisions-to-be-made.md#d002--scope-of-the-replay-artifact-identity)). The body digest is integrity, not tamper protection (R2). `run.py` does not exist yet.

## [2026-11-06] verify | EXPERIMENT 0003 complete

**[Verified]** `python3 experiments/0003-source-linked-replay/run.py` runs the five gate steps in series. RED, RED review, GREEN and the independent TEST (5/5 checks) passed. [Notes](../experiments/0003-source-linked-replay/workflow/2026-11-06/run/notes.md), [TEST record](../experiments/0003-source-linked-replay/workflow/2026-11-06/run/test-result.json)
**[Verified]** The review blocked a zero-test pass of the compiler reference step (O1). The repair added a RED test. The repaired run passed 5/5 steps. [Review](../experiments/0003-source-linked-replay/workflow/2026-11-06/run/review.md), [runner result](../experiments/0003-source-linked-replay/results/20261106T082425551626Z/result.json)
Updated the workflow record, the [EXPERIMENT 0003 page](../experiments/0003-source-linked-replay/README.md#evidence-and-limits), its overview page and the [R&D register](planning/research-and-development.md#experiment-register).
**[Unknown]** The runner directory has no own output hashes and stores absolute step paths (O2). No independent TEST of the repair is recorded. A passed EXPERIMENT does not establish production readiness.

## [2026-11-06] verify | EXPERIMENT 0003 final verification

**[Verified]** A fresh final verification tested the run.py zero-test repair. `run_test.py` passed 5 tests. The real run passed 5/5 steps. A missing Rust test name now fails the compiler reference step. [Final verification](../experiments/0003-source-linked-replay/workflow/2026-11-06/run/result.json), [runner result](../experiments/0003-source-linked-replay/results/20261106T082750423575Z/result.json)

## [2026-11-06] ingest | BAML v1 language and status

**[Verified]** Read two new captures: [release status](../raw/research/baml/v1-status-2026-11-06.md) and [language and repository](../raw/research/baml/v1-language-repo-2026-11-06.md) at pin `989676dd5169497c0d2a8d8e1d10914e987ae262`. Nothing was run.
**[Verified]** BAML v1 is a separate general-purpose language. Its release line is `baml-language-0.25.1`; no 1.0 tag exists. The v0 docs now call v0 "the legacy DSL"; v0 continues as `0.226.3`.
**[Verified]** v1 records HTTP bodies by default, with an 8 MiB truncation limit. No replay exists on the default branch; pull request #3336 is still open. Durability is draft pull request #4956. No supervision, links or monitors were found.
Created the [BAML v1 source page](sources/baml-v1.md). Corrected the v0/v1 track labels in [BAML docs](sources/baml-documentation.md), [canary compiler](sources/baml-canary-compiler.md), [compiler walkthrough](concepts/compilers/baml.md), [source registry](sources/README.md) and [language/tooling](concepts/baml-language-and-tooling.md). Added the [BAML v1 vs BEAM/OTP](concepts/baml-language-and-tooling.md#baml-v1-vs-beamotp) section. Extended the [Observatory comparison](concepts/observability-and-replay.md#baml-v1-update-pin-989676dd-2026-11-06). Updated [BAML internals](sources/baml-internals.md), [licence](sources/baml-license.md) and an evidence note under [round 3, objection 2](planning/roasting-rounds.md#2-baml-is-a-moving-baseline-with-overlapping-features).
**[Unknown]** The owner reports that v1 is maybe finished. The captures support "very far along", not "finished". Status words conflict upstream ("public beta", "private beta", "early access"). Wire-byte fidelity, vendored licences and the outcome of #4956 remain open.

## 2026-11-06: vertical integration as owner goal

**[Verified]** Captured the [BAML homepage claim](../raw/research/baml/homepage-vertical-2026-11-06.md): one toolchain from build to feature flags.
**[Requirement]** Recorded the owner goal in [vertical integration](concepts/vertical-integration.md).

## 2026-11-06: EXPERIMENT 0004 slice 1 verdict and slice 2 plan

**[Verified]** Recorded the slice 1 final review in the [0004 README](../experiments/0004-generated-replay/README.md#slice-1-verdict-2026-11-06): implementation passes with notes; the claim is REJECTED (manual change sites GEN 0 = LIB 0; no compile error caught a DRIFT).
**[Requirement]** The OWNER supersedes the slice 1 rule for slice 2. Added the [slice 2 plan](../experiments/0004-generated-replay/README.md#slice-2) and the register row in [research and development](planning/research-and-development.md).
**[Proposal]** Added the glossary terms RESPONSE RECORD, DRIFT, TYPE VERSION, RECORD SNAPSHOT and RENAME ALIAS. Nothing was run.

## 2026-11-06: EXPERIMENT 0004 slice 3 plan

**[Proposal]** Added the [slice 3 plan](../experiments/0004-generated-replay/README.md#slice-3) (README revision 7): `add <field>: <TYPE> = <constant>` and `drop <field>: <TYPE>` in the MIGRATE CHAIN, comma-separated MIGRATE CHANGES, backward derivation, consistency checks K1–K12, cases D1–D16 and a pass and reject rule. Added a register row in [research and development](planning/research-and-development.md).
**[Proposal]** Added the glossary terms MIGRATE STEP and MIGRATE CHANGE. No new OWNER question. Nothing was run.
