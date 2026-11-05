---
id: planning-build-readiness
title: Build readiness and first validation plan
kind: planning
status: proposed-not-implemented
updated: 2026-11-05
---

# Build readiness and first validation plan

**[Proposal]** Build one reproducible compiler-to-BEAM slice before broad language/UI/Observatory coverage. Important semantics remain open. **[Verified]** [EXPERIMENT 0001](../../experiments/0001-syntax-to-beam/README.md) now tests a smaller interface/pattern subset on the BEAM. It does not complete this broader plan or M0/M3. The [spec inventory](../sources/engineering-spec-v0.5.md) preserves exact requirements, phases and proposed numeric gates; the [gap queue](specification-gaps.md) retains unresolved alternatives rather than silently choosing them.

The deeper [knowledge coverage audit](specification-knowledge-coverage.md) now routes every S01-S45 group to local mechanism/source traces and separates remaining reference knowledge, language decisions and absent execution. Use it before interpreting this concise first-build map as complete language design.

## Decide the contracts that every layer depends on

| Order | Decision artifact | Why first / evidence | First validation (proposed unless marked requirement) | Spec phase anchor |
|---|---|---|---|---|
| 1 | Core grammar + evaluation/type/effect/error rules | Mixed `function`/`fn`, field punctuation and incomplete EBNF; [gaps](specification-gaps.md#blocking-language-and-abi-questions), [BAML tracks](../concepts/baml-language-and-tooling.md) | **[Requirement]** M0 typing/evaluation rules + 100 normative examples. **[Proposal]** Start examples with one record, enum/union, pure helper and prompt body; include missing/null, integers and foreign failure distinctions. | M0 before M1-M3; UI A after core |
| 2 | Versioned ABI and one source backend | Generated structs/typespecs cannot create trusted validated values; [BEAM boundary](../concepts/beam-runtime-and-interop.md) | **[Requirement]** Start with generated Elixir and the Elixir/OTP compiler. [Decision](../sources/syntax-spike-requirement.md). **[Proposal]** Pin the support tuple and test validators, errors/cancellation and source-map diagnostics. Test forged nominal/validated markers and stale schema before effects. | M3; UI B later |
| 3 | Semantic/source/artifact identity + query inputs | Lossless syntax alone does not define stable IDs; hidden inputs cause stale queries; [compiler/tooling](../concepts/compiler-and-tooling.md) | **[Proposal]** Distinguish DB revision IDs, authored spans and published artifact hashes; unsaved Unicode/comment/interface/policy edits compare incremental with clean answers and recomputation counts. | M1-M4 |
| 4 | Minimum security model + TCB | Lattice algebra, pc/errors, strict UNKNOWN and release governance unresolved; [IFC](../concepts/information-flow-security.md) | **[Proposal]** Finite lattice/property model, direct/branch/exception sink negatives, reviewed/unknown foreign fixtures; refuse unclassified sensitive egress. Do not postpone all implicit flow under P2. | P0 with M2-M3; advanced P2 later |
| 5 | Stream/error/cancellation publication contract | BAML partial output need not imply monotone immutable values; task death need not stop native/provider work; [streams](../concepts/structured-output-and-streaming.md), [runtime](../concepts/beam-runtime-and-interop.md) | **[Proposal]** Snapshot/delta/revision choice, final-validation boundary, attempt IDs/retry budget, backpressure and owner-death cases. Fixture transport first, real provider later. | M3/M5; stream extensions explicitly staged |

These are proposed dependency priorities, not newly adopted language decisions. A backend probe or finite label model may inform a decision without committing BEAML to its implementation.

## Requirement to evidence to probe map

Local requirement handles refer to [S01-S45 in the source inventory](../sources/engineering-spec-v0.5.md#section-by-section-requirement-inventory). Source evidence concerns feasibility, never completed BEAML behavior.

| Requirement / source | Supporting evidence | Open decision / first proposed probe | Phase / acceptance boundary |
|---|---|---|---|
| S02/S07-S10: lossless frontend, shared semantics, deterministic queries, useful LSP | [Compiler sources](../sources/compiler-tooling.md), [BAML canary](../sources/baml-canary-compiler.md) | Choose syntax/query boundaries; token roundtrip, malformed recovery, one same-DB diagnostic/hover/definition; fresh-vs-incremental after source/interface/schema changes; stale Unicode edit refuses unsafe rename. | M1-M4. Parser1M and later10M gates remain source targets; no measured latency. |
| S03-S06/S21/S23: types/effects/witnesses + untrusted validation across generated ABI | [Structured output](../concepts/structured-output-and-streaming.md), [BEAM interop](../concepts/beam-runtime-and-interop.md) | Specify union preference, nominal representation, missing/null, errors/exit/cancel; valid fixture decode and every malformed/forged input rejected before effect counter changes. | M2/M3; **required** end-to-end validated extraction demo. |
| S07-S09/S18: backend/Mix and semantics preservation | [Mix and backend evidence](../sources/beam-otp-phoenix.md), [compiler invariants](../concepts/compiler-and-tooling.md) | Deterministic source/maps/ABI; clean/no-change/import edit/source deletion/compiler failure leave no stale callable artifact; compare supported evaluator with generated results/errors/effect order. | M3/M8; MIR golden/differential tests are required release evidence. |
| S05/S11/S28: generation, refined shrinking, stateful traces, replayable seeds | [Property/testing sources](../sources/compiler-tooling.md#backend-locations-and-testing), [stream fixtures](../concepts/structured-output-and-streaming.md) | Define exhaustion, valid shrink relation, precondition preservation; one refinement generator reports exhaustion and one failing lifecycle trace shrinks without invalid commands. | M5/UI F; **required** seed replay +invariant-preserving shrink. |
| S12-S14/S27: optional DDD, architecture, evidence manifests | [Product contract](../concepts/product-contract.md), [IFC limits](../concepts/information-flow-security.md) | Resolve proof enum/UNKNOWN waiver; one cycle/effect rule and opaque boundary yields exact status/source/evidence; versioned event change shows compatibility failure. | M6/UI E; no arbitrary business/distributed correctness proof. |
| S22-S26/S31: UI descriptors, parser-backed analysis, safe rename/forms | [Phoenix/HEEx evidence](../concepts/phoenix-heex-integration.md) | Pin unofficial/internal parser dependency; .heex/~H Unicode/indent/nested slots/source spans; string ID +missing/empty/null form cases; dynamic event UNKNOWN; unsafe rename refused. | UI A-D; **required** all public browser entry points validate before commands. |
| S33-S37/S42-S45: labels, pc, sink policy, explicit releases, foreign classification | [Jif/effects primary notes](../sources/information-flow-security.md) | Fix algebra/TCB/interop rules; join laws +direct/implicit/error-path compile-fail fixtures; sensitive default to unknown foreign sink refuses; declassification without authority refuses. | P0 core, P1 approvals/manifests, P2 advanced analysis; scope ambiguity remains open. |
| S15/S38-S41: safe metadata, explicit context, bounded telemetry, tenant-aware Observatory | [OTel/storage evidence](../sources/observability-platforms.md) | Pin per-signal packages; command/task causality with separate supervision graph; collector outage verifies bounded memory/nonblocking business/loss counters; canary scan all sinks; actual runtime tenant-role isolation. | M7/P0 OTLP+Postgres; P1 ClickHouse after need measured. |
| S15/S40: historical PDF fixture/provider replay; expanded by R01 below | [Replay/storage synthesis](../concepts/observability-and-replay.md) | Purpose/consent/key/access/expiry/deletion model; canary fixture absent by default, explicit opt-in/revoke, version-aware object removal +DB index cleanup; do not claim scheduler replay. | M7/P2 encrypted replay; ordinary telemetry no unbounded spool. |
| S16/S17/S29/S43: reproducible performance/security/fuzz gates | [Exact source targets](../sources/engineering-spec-v0.5.md#exact-acceptance-targets-and-reproducibility-contracts) | Unify baseline/UI hardware and summary protocol; version corpora +counts +confidence; distinguish TESTED from PROVED. No benchmark is a soundness proof. | M8/UI D/P1-P2 as scoped; zero P0/P1 defects and mandatory suites required. |

## Smallest complete sequence

1. **Formal core and fixture corpus.** Close the first decision row and record what remains excluded/UNKNOWN. Keep BAML established-doc and canary semantics distinct; no compatibility claim. Document decisions with alternatives/consequences where helpful ([decision lens](../concepts/decision-consequences.md)).
2. **Compiler/runtime seam.** Lossless parse -> shared type/effect facts -> checked MIR -> one generated module +guarded API +source map -> tiny Mix host. Use a recorded provider fixture. Demonstrate rejection before effects, explicit failure/cancel cleanup and mapped diagnostics, then a single unsaved-buffer LSP path. See [detailed slice](../concepts/compiler-and-tooling.md#smallest-reproducible-vertical-slice).
3. **Small security and telemetry seam.** Integrate the scoped label/sink baseline while the IR/ABI is small; add metadata-only local OTLP+Postgres with canary/outage/tenant tests. A generated unsafe value must not already be exported before Collector cleanup. No payload/replay opt-in until policy is specified.
4. **Phoenix contract seam.** One validated command/form/event/HEEx flow, official pinned parser/source spans, unsupported dynamic fallback and safe cross-language edits. Account for disconnected/connected mount/reconnect to avoid accidental duplicate model calls.
5. **Broaden only from measured gates.** More syntax/types/providers, invariant-preserving generators/state models, architecture/DDD, mature Observatory views and ClickHouse/replay follow explicit tests and evidence. The spec's M/A/P roadmaps remain the detailed gate source, not a claim all work fits the first slice.

## What this research does not settle

**[Verified]** EXPERIMENT 0001 records its local Rust/Elixir/OTP tuple, generated source, BEAM execution tests and scoped exact-boundary results. It reuses no BAML code. **[Unknown]** A production support tuple, broad property/fuzz suite, performance benchmark, live model call, security proof and storage deletion result remain absent. Preserve the distinction between this small probe and the broader proposed validation slice.

## Central typed replay slice from R01

**[Requirement]** The [later request](../sources/typed-replay-requirement.md) makes full typed error-surrounding replay central. It is a new target, not deferred merely because the historical PDF staged optional replay later. **[Proposal]** Add a minimal authorized REPLAY CAPSULE and TYPED ERROR to the compiler/runtime vertical slice before broad provider/concurrency support. Use synthetic permitted fixtures first; no secret capture or live replay effects.

1. Declare the supported complete scope and admission contract; define capture-required inputs, contextual identities and effect boundaries.
2. Preserve source/build/dependency/schema/policy versions plus unsaved edit/query history where relevant. Preserve raw-invalid input without inventing VALIDATED VALUES.
3. Record initial state, attempted effects and observed outcomes durably under an explicit crash/acknowledgment model. Keep unknown external outcomes unknown.
4. Execute an isolated REPLAY RUN with typed recorded effect substitution. Assert capture completeness, runner status and original-error reproduction independently.
5. Exercise missing/corrupt entries, mid-effect crash, journal outage, stream revisions, tenant denial and version mismatch. Follow the [per-context acceptance matrix](../concepts/typed-errors-and-replay.md#acceptance-by-context).
6. Evaluate broker/consumer throughput only after the [delivery/acknowledgment gates](../concepts/event-flows-and-backpressure.md) are satisfied. Standard BroadwayKafka always-ack failure behavior cannot silently become the no-loss journal contract.

These are proposed acceptance checks. No replay implementation, durable capture test or throughput result exists.
