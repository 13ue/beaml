---
id: concept-static-architecture-evidence
title: Architecture graphs, effects and contract evidence
kind: synthesis
status: proposed-not-implemented
updated: 2026-11-05
---

# Architecture graphs, effects and contract evidence

**[Requirement]** Structural architecture checks use symbol/dependency graphs; semantic checks use typed HIR/MIR/effects. Taint analysis is conservative and opaque calls can remain inconclusive. Contract manifests need obligation/source/checker/status/evidence/runtime-hook metadata; proof statuses and release dispositions must be explicit. [Spec pp.4–5 §§8–9; pp.10,14 §§27,43–46](../sources/engineering-spec-v0.5.md)

## Structural rules are graph queries with a declared scope

**[Verified]** ArchUnit imports Java bytecode into class/package dependency objects and supplies layer/slice/cycle checks; its generic cycle API permits metadata on edges. Its default empty-selection failure prevents a rule from passing accidentally after a package rename stops matching. This is an architecture-test precedent, not a BEAML effect/IFC checker. [Guide1.5.1](https://www.archunit.org/userguide/html/000_Index.html#_the_core_api), [cycle API](https://www.archunit.org/userguide/html/000_Index.html#_the_cycle_detection_core_api), [empty selector](https://www.archunit.org/userguide/html/000_Index.html#_fail_rules_on_empty_should)

**[Proposal]** BEAML should derive nodes/edges from resolved compiler identities, not filename regex alone. Node kinds may be modules/definitions/packages/contexts; edge kinds distinguish import, signature type reference, call, implementation, generated wrapper, runtime capability and dynamic unknown boundary. Selectors can use names/annotations, but the rule must say what it selects and whether it examines direct or transitive edges.

A no-cycle check can compute strongly connected components on the declared edge relation; a forbidden-dependency rule checks selected source/target edges or reachability. Return an actual cycle/path with source spans, not only a yes/no. Bounded diagnostic enumeration must not become bounded analysis silently; distinguish “all edges analyzed, report truncated” from “analysis stopped”. Empty matches, unresolved imports and excluded generated/foreign modules require explicit outcomes.

Illustrative non-executed graph: `billing.domain -> helper -> billing.web`. A direct-import rule on domain may pass while a transitive reachability rule fails. Neither answer is inherently wrong; the declared rule semantics decides. Match counts and graph/capability versions belong in evidence so a stale selector cannot produce vacuous safety.

## Effects are not just package dependencies

**[Proposal]** Infer a function's supported effect summary from its direct operations plus callee summaries, iterating over recursive call components to a fixed point in a defined finite effect domain. Check actual effects are a subset of its allowed declaration. For `domain.f -> helper.g` where g directly calls network, f inherits network even if neither imports a module named HTTP. The algorithm's termination/unknown policy depends on BEAML's explicit effect semantics. [Effect foundations](types/refinements-and-effects.md), [compiler/query mechanics](compilers/incremental-compilation-and-source-identity.md)

Higher-order calls, dynamic dispatch and foreign functions need checked summaries/dictionaries or conservative unknown. A reviewed manifest must identify exact package/version/export and assumptions; matching a function name is not evidence of its effects. Changing a summary invalidates callers and architecture results. A trusted opaque summary narrows the TCB claim; it does not prove the external code behaves accordingly.

## Taint/pc flows require a different graph

**[Requirement]** Value labels and program-counter restrictions propagate through derived data/errors/control flow and are checked at sinks; unknown foreign boundaries cannot silently certify sensitive egress. [IFC contract](information-flow-security.md)

**[Inference]** A dependency graph cannot prove absence of leakage. A pure-looking function may derive a public branch choice from a secret, while a network-capable function may send only approved public data. BEAML needs typed data/control-flow summaries and sink policy, with interprocedural approximation and explicit declassification—not merely a forbidden package rule. [IFC mechanism and limitations](information-flow-security.md), [typed MIR boundary](compilers/baml.md)

**[Proposal]** Keep structural violation, effect violation, label-flow violation and unknown analysis distinct diagnostic categories. Propagate their source evidence through generated helpers and runtime guards. Untracked Elixir/macros/NIFs/reflection are classified or blocked under policy; architecture selectors cannot downgrade them to safe.

## An evidence manifest records a scoped claim

**[Requirement]** Source vocabulary drifts between PROVEN/ENFORCED and PROVED/RUNTIME_ENFORCED, with TESTED/UNKNOWN/VIOLATED appearing in different tables. Preserve the distinction until a canonical enum/migration is accepted. [Original statuses](../sources/engineering-spec-v0.5.md#proof-status-vocabulary-do-not-collapse-these), [gap queue](../planning/specification-gaps.md)

**[Proposal]** A machine-readable record should separate at least:

| Field group | Meaning / why it matters |
|---|---|
| Obligation identity and normalized rule | Which exact invariant/architecture/flow/schema obligation is being evaluated |
| Source/semantic/artifact IDs | Where it came from and which built program/source map it describes |
| Checker/rule/logic/version and options | Which supported procedure produced the verdict |
| Assumptions/TCB and analyzed scope | Foreign summaries, supported syntax, exclusions, bounds and solver model |
| Status plus reason | Static discharge, runtime guard, sampled test, counterexample or unknown; never inferred from missing evidence |
| Evidence references | Proof/checker artifact if applicable, counterexample, corpus/seed/results, graph path or descriptor diff |
| Runtime hook/guard | Exact guarded export/call site and failure behavior when static reasoning ends |
| Release disposition/waiver | Accept/reject/approved exception with scope/expiry/authority, separate from epistemic status |

Only the core fields named in the PDF are requirements; the grouping/additional fields are proposals. Signing/storing a record authenticates provenance under its trust assumptions, not the truth of its claim. A TESTED record must name corpus/coverage; a runtime-enforced record must point to a guard actually inserted on the relevant paths; UNKNOWN must retain unsupported/timeout/opaque reasons.

## Counterexamples and waivers are first-class outputs

**[Proposal]** Structural/effect failures return a minimal source path/cycle; type/refinement/property failures return a reproducible counterexample where available; IFC failures identify the source/pc/sink path without leaking secret payloads. A display that truncates a graph must say so. Security evidence is itself policy-controlled data. [Verification](testing/compiler-verification.md), [observability privacy](observability-and-replay.md)

A release policy may accept a scoped waiver under the specification's governance, but the obligation remains UNKNOWN/violated/tested as applicable. Do not map waived UNKNOWN to PROVEN, and do not treat a stored baseline of violations as new safety. Invalid/stale checker/source/interface/manifest identities require re-evaluation or explicit refusal.

## First conformance evidence

**[Proposal]** Build one real pure-domain rule with direct/transitive counterexamples, an import cycle with spans, an empty selector, a recursive effect summary and an opaque foreign call. Emit deterministic manifests with exact statuses and check invalidation after changing a callee effect/schema/policy. Add one generated runtime guard and show its evidence maps to actual rejecting behavior before domain effects. No graph checker, proof engine or manifest format is implemented here.
