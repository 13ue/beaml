---
id: planning-specification-gaps
title: Specification gaps and decision queue
kind: planning
status: unresolved
updated: 2026-11-05
---

**[Unknown]** Open semantics and **[Proposal]** next artifacts are separated below; source requirements are cited as evidence.

# Specification gaps and decision queue

**[Requirement]** The later [syntax spike request](../sources/syntax-spike-requirement.md) selects syntax for a small EXPERIMENT. It uses exact data interfaces, partial record patterns, unparenthesized function heads and parenthesized calls/constructors. **[Unknown]** These choices do not settle the complete grammar, generic inference, effects or production GENERATED ABI listed below.

These are unresolved specification decisions and KB interpretations, not bugs in an implementation. Each row separates the source's explicit open question from analysis of what must be settled. Page numbers are physical PDF pages; [source inventory and full evidence](../sources/engineering-spec-v0.5.md). Research can inform decisions; it cannot silently authorize them.

The [knowledge coverage audit](specification-knowledge-coverage.md) distinguishes missing reference knowledge from open BEAML decisions and unexecuted validation. Deep mechanism pages explain alternatives; they do not silently close the decisions listed here.

## Blocking language and ABI questions

| Question | Evidence | Implication / next artifact (KB recommendation) |
|---|---|---|
| Complete grammar and formal semantics | p.1 §2 says full grammar future v0.4; p.7 §16 asks for typing judgments, evaluation, trait resolution, MIR invariants, query protocol; p.8 §22 still illustrative UI syntax. | Produce versioned core EBNF + typing/evaluation rules + 100 normative examples before M0 exit; appendix presence is not evidence grammar was delivered. |
| Syntax consistency | p.1 uses `function`, colon fields, generic params/effect sets; p.12 uses `fn`, fields without colons, label annotations and effect arguments. | Define canonical tokens/label/effect grammar; do not implement all examples as simultaneously normative syntax. |
| Structural subtyping and generic variance | p.7 §15 explicitly open. | Define width/depth rules, mutable positions if any, unification/coercion, diagnostics and negative cases. |
| Traits across packages | p.2 §3 coherent/no overlap; p.7 §15 orphan rules and associated normalization open. | Publish coherence/orphan algorithm and package identity; associated types phase 2. |
| Refinement predicate fragment and unknown policy | pp.2,7 §§3,15. | Select decidable core/timeout budget, explicit checked conversion, solver assumptions and UNKNOWN treatment. |
| Schema witness strategy | p.2 §3 permits monomorphization or typed dictionary. | Decide generated ABI/reification format, generic separate compilation and schema capability fingerprints. |
| Streams and resource ownership | p.2 §3 typestate, affine handles later; p.7 §15 partial field revision open. | Specify field readiness/revision, cancellation/error states, ownership/cleanup and validated-complete boundary. |
| BEAM interop | p.7 §15 atom safety, serialization/cancellation/opaque effects open; p.13 §37 reviewed manifests/opaque handles. | Define atom budgets, nominal/sealed representation, process cancellation and error conversion; foreign struct construction cannot confer validation. |
| Handlers | p.7 §15 says explicit dictionaries first, algebraic continuations later. | Specify dictionary calling convention and propagation before effectful backend implementation. |
| Schema/API/event evolution | pp.4,7 §§7,15; p.8 §21 versioned ABI. | Specify compatibility relation, version negotiation/migration and generated API break detection. |
| Repository crate granularity | p.6 §13 lists modules but permits combining. | Start with semantic ownership boundaries, not obligatory one-crate-per-box scaffolding. |

## UI and tooling questions

| Question | Evidence | Implication / next artifact (KB recommendation) |
|---|---|---|
| Phoenix/HEEx parser support | pp.9,11 §§24,31 official parser required, compatibility matrix open. | Pin supported Phoenix/LiveView/Elixir versions; demonstrate public/private parser API behavior and mapping for .heex/~H. |
| Supported static subset | pp.8-9 §§22,24-25; p.11 §32. | Enumerate literal event/component/assign transformations; dynamic keys/metaprogramming and unsafe rename explicitly unknown/refused. |
| Type metadata/descriptor transport | p.11 §31 open. | Define schema descriptor wire and Elixir module metadata, source ID persistence and cache invalidation. |
| Props/slots/dynamic components | p.11 §31 open. | Specify attr defaults, slot multiplicity/:let shape, optionality and dynamic fallback. |
| Forms | p.9 §26 requires distinct optional/missing/empty/null semantics but supplies none. | Specify input normalization matrix and nested/union/error roundtrips; browser strings are never already nominal values. |
| ABI completeness | p.8 §23 lists descriptors/decode_event/form/change/assign/fields but example calls put_error. | Publish exact exports/types/error schemas and stable descriptor version; clarify whether example helper is generated. |
| LSP version and staleness | p.3 §5 chosen protocol release not named; p.9 §25 multilang rename. | Pin protocol/capability matrix, unsaved overlay identity and cross-language edit version checks. |
| Compile-time vs CI enforcement | p.11 §31 explicit open. | Separate interactive diagnostics, build blockers, strict production policy and approved exceptions. |

## Security and Observatory questions

| Question | Evidence | Implication / next artifact (KB recommendation) |
|---|---|---|
| Exact lattice and join | p.12 §§34-35 describes dimensions and purpose/recipient restrictions, not ordering/algebra. | Define bottom/top, set ordering, join/meet, policy entailment, defaults and unknown labels; property-test lattice laws and contextual sink decisions. |
| pc analysis minimum vs rollout | p.12 §35 requires v1 rejection of analyzable secret-dependent public output; p.14 §45 puts advanced implicit flow in P2. | Decide what basic P0 implicit-flow support is mandatory and what conservative rejection is allowed; do not defer all pc flow to P2. |
| TCB and guarantee | p.12 §33 requires declared TCB; p.14 §46 formal model scope. | Enumerate compiler/runtime/manifests/policy engine/exporters/adapters/operators and side channels; define threat model and explicit trust assumptions. |
| Unknown interop and strict mode | p.13 §37 UNKNOWN or blocked; p.14 §45 fail closed unclassified sensitive egress. | Define classification vs enforcement outcome and reviewed manifest provenance/versioning; UNKNOWN cannot silently authorize sensitive output. |
| Declassification stages | p.12 §36 requires reviewed policy/capability/audit; p.14 §45 approvals P1, vetted masking P2. | Specify P0 behavior (likely no sensitive release without reviewed supported capability) as a decision, not inferred permission. |
| Authorization versus public downgrade | p.13 §37 allows user-scoped PII by explicit principal policy. | Define tenant/principal/purpose context lifetime and checks across async process messages, session changes and cached render values. |
| Release-status vocabulary drift | pp.4-5 §9 PROVEN/ENFORCED/TESTED/UNKNOWN/VIOLATED; pp.10,14 §§27,46 PROVED/RUNTIME_ENFORCED/TESTED/UNKNOWN. | Choose canonical enum/migration; retain violation/rejection state and scoped proof/evidence metadata. |
| Security manifest stage | p.14 §43 says output contains manifest; §45 places security manifests/CI in P1. | Clarify minimal P0 metadata vs P1 release artifact and classified-callsite gate. |
| Event identity/privacy | p.13 §40 requires stable semantic/source IDs but prohibits hashing secrets into stable identifiers and warns customer IDs/paths/templates sensitive. | Define safe event IDs/attributes, source-map access, PID encoding and metadata categorization; avoid unsafe auto-capture. |
| Retention and deletion | p.13 §41 defaults are proposals; opt-in replay encrypted/scoped/deletable. | Define tenant policy, consent, encryption/key ownership, deletion propagation/backups, TTL and access audit; source provides no compliance guarantee. |
| Outage semantics | p.14 §41 ordinary lossy nonblocking telemetry vs separate durable security audit. | Define buffer bounds/drop policy/loss metrics and audit failure mode; do not make ordinary export block commands. |
| Storage rollout | p.13 §39 ClickHouse reference, small Postgres permitted; p.14 §45 P0 Postgres/P1 ClickHouse. | This is compatible staged guidance, not a contradiction. Decide measured migration thresholds rather than assume both databases needed initially. |
| Replay | p.5 §10 and p.14 §41 prohibit conflating provider fixtures with scheduler replay. | Specify fixture eligibility, nondeterminism limits, version capture, secrets/consent and failure semantics. |
| Secret memory handling | p.13 §38 feasible zeroization; BEAM GC no blanket guarantee. | Document runtime copies/process mailboxes/inspect/dumps/loggers and operational controls with a bounded assurance claim. |

## Acceptance ambiguities and priorities

1. **Three roadmaps, no combined dependency graph.** M0-M8, UI A-F, security P0-P2 have separate gates (pp.7,11,14). Recommendation: build a single dependency map before ticketing; do not treat all P0 work as either already implemented or part of baseline M0.
2. **P0/P1 has two meanings.** §12 uses defect severity; §45 uses feature-rollout stages (pp.6,14). Recommendation: name namespaces in planning to avoid confusing a P1 feature with a release-blocking defect.
3. **Benchmark environments differ.** Baseline requires Linux/8 vCPU/NVMe/p50-p95-max-CI; UI says 8 performance cores/SSD/p50-p95-p99 and warm/cold reporting (pp.5,10). Recommendation: preserve both source contracts and choose a pinned shared protocol before results comparison.
4. **99% semantic accuracy is not a soundness waiver.** UI accuracy corpus target and zero known false-safe classification coexist (p.10 §29). Unsupported/inconclusive cases must remain UNKNOWN even if accuracy aggregates improve.
5. **Fuzz milestones differ by stage.** Parser M1 is 1M; hardening M8 and broader UI/security gates are 10M (pp.7,10,14). These are stage-specific targets, not measured achievements.
6. **Waiver governance open.** Baseline UNKNOWN accepts explicit waiver or reject; taint waiver governance open (pp.4,7). Recommendation: version waiver scope/expiry/reviewer/evidence and ensure a waiver never changes proof status.

## Research followups ranked by decision leverage

1. Pin BEAM/Phoenix and obtain tiny end-to-end boundary experiments: schema validation, events/form ABI, official parser source spans, atom safety, async cancellation. This tests M3/UI B-C feasibility before broad surface expansion.
2. Compare BAML's actual schema/stream semantics with the proposed BEAML trust states; list adopted ideas and deliberate BEAM differences, without assuming language compatibility.
3. Select a minimal Rust frontend/query strategy and document durable semantic/source identity across edits, lowering and regenerated artifacts.
4. Establish a small formal information-flow model and threat boundary before treating policy annotations as security. Include pc flows, interop UNKNOWN, errors and declassification.
5. Measure a local OTLP+Postgres telemetry path with strict safe attributes, bounded loss under outage and canary sinks; postpone ClickHouse/replay until demonstrated need and explicit privacy policy.
6. Ground shrinking/generator and state-machine semantics in reproducible reference implementations, especially refined types, exhaustion and precondition-preserving trace reduction.

## Later typed replay requirement R01

**[Requirement]** The [2026-11-05 request](../sources/typed-replay-requirement.md) expands the historical fixture-only replay target. **[Unknown]** Define full surrounding scope, required/forbidden capture, admission and durable append acknowledgment, crash windows, contextual identities, compiler edit/query capture, provider chunk/attempt capture, causal scheduling model, completeness evidence, typed error equality, version/upcaster support, expiry/deletion and safe isolation. Capture failures themselves have a fault boundary; no recursive no-loss claim is established. Keep original-error reproduction, runner success and capture completeness separate. [Design](../concepts/typed-errors-and-replay.md), [transport gates](../concepts/event-flows-and-backpressure.md)
