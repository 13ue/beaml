---
id: concept-schema-api-evolution
title: Schema, generated API and event evolution
kind: synthesis
status: proposed-not-implemented
updated: 2026-11-05
---

# Schema, generated API and event evolution

**[Requirement]** Generated event schemas are versioned and checked for breaking changes; generic schema capabilities, imported interfaces, generated UI ABI and metadata must participate in version/invalidation policy. The precise compatibility relation is open. [Spec pp.2,4,7–8 §§3–4,7,15,21](../sources/engineering-spec-v0.5.md), [decision queue](../planning/specification-gaps.md)

## Compatibility is directional and layer-specific

**[Proposal]** Name producer/writer and consumer/reader versions, transport/representation and supported history before judging a change. “Compatible” can mean any of the following; none implies all the others:

| Layer | Question |
|---|---|
| Parse/wire | Can this reader decode bytes/data produced under that writer schema? |
| Typed source API | Do existing callers/constructors/pattern matches still type-check? |
| Generated ABI | Do host module/export/argument/result/error representations agree? |
| Refinement/domain | Do decoded values still satisfy current invariants and units/meaning? |
| Effects/security | Are recipients, capabilities, labels and authorization assumptions preserved? |
| Operational | Can mixed versions, in-flight messages, stored events, snapshots and rollback coexist? |

A backward-compatible reader usually must accept old writer values; an updated API must not demand stricter inputs from existing clients or produce results/errors they cannot handle. These are proposed behavioral relations, not a universal algorithm for arbitrary refinements/effects. State which relation a checker implements and return UNKNOWN when it cannot establish it.

## A concrete reference: Avro writer/reader resolution

**[Verified]** Avro1.12.0 resolves writer and reader schemas: record fields match by name; extra writer fields can be ignored; a reader-only field needs its reader default; enum/union resolution has explicit matching/default/order rules. Aliases can map renamed fields/types. Parsing canonical form removes parsing-irrelevant information to support a parsing identity; it does not encode all business policy. [Schema resolution/canonical form](https://avro.apache.org/docs/1.12.0/specification/#schema-resolution)

**[Inference]** The useful BEAML lesson is an explicit version-pair resolution relation. It is not permission to treat any added field as harmless. A defaulted `currency` may decode but change money interpretation; an optional field still needs distinct missing/null semantics if the contract requires them. Renaming a nominal domain ID is not necessarily a display alias.

**[Verified]** Protobuf warns against reusing old tag numbers and reserves deleted tags because stored data and mixed/rolled-back versions can survive. Its evolution rules depend on encoding. [Best practices](https://protobuf.dev/programming-guides/dos-donts/), [proto3 update rules](https://protobuf.dev/programming-guides/proto3/#updating)

**[Proposal]** BEAML need not adopt Avro/Protobuf. Choose its representation and derive rules from it, including binary/JSON/host-term differences. Keep stable schema/event identity separate from display names; a changed fingerprint signals difference, while a compatibility algorithm explains whether that difference is acceptable.

## Worked change questions, not automatic answers

| Proposed change | Compatibility check BEAML must define |
|---|---|
| Add required input field | Can all old callers supply it, or is a semantically valid default/migration specified? |
| Add output/event union variant | Can old consumers decode it and exhaustive handlers respond safely? |
| Tighten interval/refinement | Which historical values are excluded; is a checked migration required? |
| Rename field/type | Does encoding use names/tags; are aliases/version adapters allowed; nominal identity preserved? |
| int range/Decimal/units change | Can values be represented without silent loss or changed meaning? |
| Add/remove/default nullable field | Distinguish absent/null/default provenance and host constructors |
| Add error outcome/effect | Can callers handle it; does the prior purity/recipient/capability contract still hold? |
| Change prompt/parser union order | Do ambiguous historical/model outputs resolve differently despite identical set-like type? |
| Change security label/purpose | Does the new policy permit only authorized flows across all active versions? |
| Change generated export/argument/witness layout | Does the host descriptor ABI negotiate or reject before execution? |

**[Inference]** Prompt and parse behavior belong in a model contract version when users rely on interpretation, not merely schema shape. BAML source distinguishes canonical unions from parser scoring/preference; matching a type fingerprint alone would miss that. [BAML boundary](compilers/baml.md#3-type-algebra-and-parsing-preference-are-different)

## Persisted events and live messages need different horizons

**[Proposal]** Maintain an explicit compatibility matrix across all supported persisted writer versions, not only the previous release. Read/transform historical events and snapshots through a deterministic versioned adapter. Do not “fix” history by silently interpreting old fields under new business semantics. Migration changes need their own validation/counterexamples, provenance, rollback/backup/deletion policy and operational evidence.

For in-flight BEAM calls/messages, pin the descriptor/version used when the call starts; reject incompatible results rather than decode using whichever module was loaded most recently. Host/runtime/compiler versions, schema capability versions and application versions are separate. A rolling deployment must specify mixed-version communication and supported rollback windows. [Upgrade boundary](beam-runtime-and-interop.md#upgrade-is-a-protocol-problem-too)

## Small compatibility artifact and conformance corpus

**[Proposal]** A descriptor can record format/language/compiler/ABI version, stable schema identity, field/variant representation, optional/missing/default rules, constraints, error/effect/label surface and referenced capabilities/interfaces. Its exact schema is not chosen here. Store normalized public descriptor diffs plus a checker verdict scoped to writer/reader versions and transport.

A minimum corpus should include add/remove/rename/default/null, unknown fields/variants, numeric limits, refined invalid history, old snapshots, stale host ABI, parser-preference changes, updated effects/labels and rollback. Exercise actual generated entry points; static descriptor comparison and runtime decode outcomes are separate evidence. Unsupported migration semantics remain UNKNOWN until reviewed. [Verification](testing/compiler-verification.md), [contract manifests](static-architecture-and-evidence.md)

No format, schema registry, migration language or compatibility checker has been adopted or run.
