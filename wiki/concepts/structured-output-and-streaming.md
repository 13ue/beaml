---
id: synthesis-structured-output-and-streaming
title: "Structured output and streaming"
kind: synthesis
status: proposed
updated: 2026-11-05
---

# Structured output and streaming

Status: BAML source synthesis plus explicitly labeled BEAML design questions. Retrieved 2026-11-05. Established documentation is unversioned; compiler source is pinned in [provenance](../../raw/research/baml/provenance.json).

## Established BAML documentation facts

**[Verified]** This section summarizes checked upstream sources, without a BEAML conformance run.

Output-schema text is generated from a function's return type using `ctx.output_format`. It is prompt guidance tailored for model consumption, not a claim that every provider uses constrained JSON Schema decoding. Its rendering has customization options. [Output format](https://docs.boundaryml.com/ref/prompt-syntax/ctx-output-format)

The pinned flexible-parser API takes output-format metadata, a target type, raw text and an `allow_partials` flag, returning values with flags. Its README names surrounding-text extraction, field aliases, coercion, array wrapping and constraints. Thus successful parsing can involve interpretation rather than a byte-for-byte JSON decode. [Parser source](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/engine/baml-lib/jsonish/README.md)

The streaming guide distinguishes generated partial types from final validated types. Numbers wait for completion; strings may grow incrementally. Final retrieval returns the original declared result type. The docs' streaming controls are summarized below. [Streaming](https://docs.boundaryml.com/guide/baml-basics/streaming)

| Control | Documented partial-output behavior |
|---|---|
| Default | Partial nullable values |
| `@stream.done` | Publish a value only when complete |
| `@stream.not_null` | Delay its containing object until that field is available |
| `@stream.with_state` | Carry incomplete/complete metadata |

Streaming annotations govern partial representation; they do not change the function's final return type. Atomic list-element/union annotations allow incremental lists of completed items. These are delivery constraints, not proof that invoking an external tool as soon as an item appears is safe. [Semantic streaming](https://docs.boundaryml.com/guide/baml-basics/streaming#semantic-streaming)

Hard assertions and non-raising checks differ. The docs say failed top-level assertions raise; failed asserted values inside containers may be removed. Checks preserve data and expose validation outcomes. BEAML must decide whether silent cardinality changes fit its contracts. [Checks/asserts](https://docs.boundaryml.com/guide/baml-advanced/checks-and-asserts)

The established type page documents ordered union parsing (a numeric string can choose a different branch). Canary's type algebra is set-like while its type-system document explicitly preserves LLM parsing order as a boundary exception. Type normalization must preserve a separate parsing preference if compatibility is intended. [Types](https://docs.boundaryml.com/ref/baml/types), [pinned type system](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/TYPE_SYSTEM.md#baml-subtyping-cases)

## Pinned canary differs: shared type and parser defaults

**[Verified]** The inspected canary uses `Stream<T>.next -> T | Done` and `final -> T`, not the established SDK documentation's separate generated partial type. Its parser has separate partial/missing-complete defaults: incomplete strings may default empty and nullable/containers null/empty; completed required-string omissions still error. The source fixture explicitly contrasts partial id-only text yielding a temporary empty name with completed id-only JSON failing. Canary declaration attributes include `@stream.must_exist` rather than assuming the older documented attribute set. These are inspected source assertions, not executed results. [Mechanism and exact source/fixture links](compilers/baml.md#6-shared-t-does-not-mean-a-complete-response)

**[Inference]** Shared runtime T does not certify field readiness, explicit-null provenance, domain validation or permission to execute tools. BEAML's `Parsed`/`Validated`/`Complete` requirements remain independent. Updated syntax/type/runtime caveats are in the [deep source note](../sources/baml-internals.md); historical raw captures are unchanged.

## BEAML design hypotheses and unresolved contracts

**[Proposal]** These questions guide a future design; none is chosen here.

These are proposals/questions, not existing language features:

1. Represent partial and final results as distinct types; absence, explicit null, incomplete text and invalid data need distinguishable states where contracts require them.
2. Specify whether emitted data is a snapshot or a delta; whether earlier values can be revised/retracted; and how union branch ambiguity is represented. The inspected docs do not establish a general monotonicity guarantee.
3. Keep parse repairs/coercions and validation outcomes observable. A result's schema validity does not prove factual correctness, trustworthiness, authorization or domain invariants.
4. Carry security labels through partial fields, speculative union branches, schema metadata and validation/filtering decisions. Publish only under the sink policy for that revision; withdrawing a value cannot undo disclosure.
5. Define retry/fallback after stream publication: attempt identity, duplicate suppression, replacement versus failure, cancellation, completion and billing. Do not concatenate retries into one apparently monotone stream without an explicit contract.
6. Separate a completed data item from an authorized effect. Tool execution needs a validated final/committed command plus policy and idempotency rules; an atomic stream item alone is insufficient.
7. Bound parser input size, nesting, buffering and repair work. Test malformed/truncated responses and cancellation so BEAM supervision is not asked to recover from unspecified parser behavior.

## Minimal evidence before adoption

**[Proposal]** The following checks are future acceptance evidence.

A deterministic fixture corpus should cover prefix/suffix prose, malformed JSON, aliases, union ambiguity, missing/null, nested recursion, coercion, failed checks/asserts and container cardinality. Replay token partitions through the partial parser; verify final equivalence, annotation gates and cancellation. Add explicit revision/deduplication fixtures before a streamed value can trigger an external effect. No such corpus was executed in this research pass.
