---
id: concept-typestate-schema-witnesses
kind: mechanism-guide
status: researched-and-proposed
updated: 2026-11-05
---

# Typestate, ownership and schema witnesses

**[Requirement]** Generic model outputs require Schema evidence, either monomorphized or passed as typed dictionaries. Proposed states include Pending/Streaming/Validated/Complete; affine stream ownership is later. Untrusted→Parsed→Validated→Refined transitions are explicit and error-bearing. [Spec S05/S06](../../sources/engineering-spec-v0.5.md). All examples below are unexecuted pseudocode, not normative BEAML syntax.

## A generic decoder needs operational knowledge of T

**[Proposal]** Parametric `decode<T>(json)` cannot inspect a type-erased T to discover fields. Consider `decode<Invoice>` versus `decode<Customer>`: identical JSON may contain enough data for one, both or neither, and nominal/refinement rules differ. A candidate evidence interface is:

```text
Schema<T> = {
  descriptor: TypeDescriptor,
  decode: Json -> Result<Parsed<T>, DecodeError>,
  validate: Parsed<T> -> Result<Validated<T>, ValidationError>,
  fingerprint: SchemaVersion
}
extract<T>(schema:Schema<T>, provider:Provider, text:String)
```

This separates prompt rendering guidance, decoding and validation. Schema<T> must correspond to T; passing Customer's descriptor under Invoice's decoder is not an acceptable erased ABI shortcut. Deriving for `List<T>` recursively consumes Schema<T>, with recursion/cycle handling for recursive types and explicit optional/union preferences. [Trait evidence](traits-evidence-and-coherence.md) supplies a plausible lowering mechanism; [BAML schema/stream distinctions](../structured-output-and-streaming.md) are implementation inspiration, not an adopted contract.

**[Proposal]** Monomorphization creates a specialized extract_Invoice with known schema; dictionary passing keeps one generic body and passes Schema<Invoice>. Specialization can simplify calls but increases code size and needs a closed set or separate-compilation strategy. Dictionaries support open generic boundaries but need versioned layout/identity and trusted constructors. Both can coexist as an optimization only after semantic equivalence is defined; stable source/operation IDs must not accidentally multiply or disappear through specialization. Neither representation creates factual truth from a schema.

## Typestate restricts legal operations; it does not erase aliases

**[Verified]** [Strom/Yemini's1986 typestate concept](https://research.ibm.com/publications/typestate-a-programming-language-concept-for-enhancing-software-reliability) makes permitted operations context/state-dependent. **[Proposal]** Candidate APIs might require `finish:Stream<Streaming,T> -> Result<Validated<T>,Error>` and refuse direct `execute:Parsed<T>`. This prevents calling a complete-only operation when a static state says partial.

But consider:

```text
s1 = start()
s2 = s1                 -- alias
finish(s1)
read_next(s2)            -- stale alias if handle was not consumed
```

A phantom parameter alone cannot make the last call invalid if copying remains legal. An affine discipline allows at most one use/ownership transfer, with dropping permitted; a linear one requires exactly one consumption under its rules. **[Verified]** [GHC 9.12.2 linear types](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/linear_types.html) uses an explicit multiplicity-one arrow and remains experimental; its lazy-language consumption condition is not BEAM handle ownership. **[Proposal]** Until affine checking exists, runtime owner/reference/state checks must prevent duplicate finish/read/cancel operations and reject foreign forged handles.

## Validation state and completion state are different dimensions

**[Proposal]** A completed provider transport can still produce invalid JSON; a partial stream can expose a field that conforms locally while the final aggregate later fails. Avoid treating Complete as synonymous with Validated. One candidate product is transport state × parse/validation state, with explicit transitions and terminal failure/cancel states. Another is distinct API types with no public constructors. The spec has not chosen either.

For each transition record: owner, input state, resource consumption, output/effect, failure, cleanup, and publication permissions. If a streamed amount changes from 1 to 10, a consumer cannot undo an effect already triggered by 1. A validated final command needs a commit/authorization/idempotency boundary distinct from a partial preview. Schema version changes midflight should either pin the old evidence or fail explicitly, not reinterpret partially delivered values.

## Trust and privacy boundaries

**[Requirement]** Ordinary Elixir structs do not confer trusted BEAML status; sensitive data labels persist and unknown foreign behavior is classified. **[Proposal]** Keep decoder/witness/handle construction scoped; include artifact/schema IDs and integrity checks at generated public APIs where needed, while admitting trusted VM code can bypass ordinary conventions. Do not expose a generic `cast_state` or unchecked `deserialize_validated`. A public schema descriptor can itself contain sensitive field names/descriptions; publication is a sink-policy question, not justified by its being type metadata. [Runtime boundary](../beam-runtime-and-interop.md), [IFC](../information-flow-security.md).

## Validation probes

**[Proposal]** Compare specialized and dictionary decoding on the same corpus; swap descriptor/witness versions and demand rejection. Test recursive schemas, missing/null, ambiguous unions, nominal IDs/refinement failure and generator-derived values. Exercise alias duplication, duplicate finish/cancel, late provider reply, owner death, buffer exhaustion and partial revision after publication. **[Unknown]** Affine syntax/borrowing, cross-process ownership transfer, state-product design, partial revision promises and Schema ABI remain unselected; current repository supplies reference knowledge, not working enforcement.
