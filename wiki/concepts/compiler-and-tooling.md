---
id: concept-compiler-tooling
title: BEAML compiler and tooling feasibility
kind: synthesis
status: proposed
updated: 2026-11-05
---

# BEAML compiler and tooling feasibility

**[Requirement]** The supplied specification proposes a Rust frontend, shared semantic database, typed HIR/MIR and generated Elixir/Erlang, with source navigation across CLI/editor/runtime. **[Proposal]** This page turns that direction into a small evidence-producing design; it does not declare an implemented compiler or select dependencies. [Product contract](product-contract.md), [source inventory](../sources/engineering-spec-v0.5.md)

## Semantics must precede parser compatibility

The source has grammar/version drift and mixed function/field spellings. Decide one canonical BEAML syntax before treating examples as a conformance corpus. Keep unsupported examples with explicit expected diagnostics until resolved. [Specification gaps](../planning/specification-gaps.md)

**[Unknown]** The canonical keyword for variant declarations remains open. [D001](../planning/decisions-to-be-made.md#d001--enum-or-type-declarations)

| Discriminator | Established BAML documentation | Pinned BAML canary | BEAML decision |
|---|---|---|---|
| Function surface | `function Name(arg: Type) -> Type` plus client/prompt | General code bodies and synthesized LLM companions | Canonical `function` versus `fn`; whether prompt functions are one body form |
| Field surface | `field Type` | Inspected fixtures use colon fields/config and backtick interpolation; full grammar still requires conformance scope | Colon fields versus no-colon extension examples |
| Types/effects | Typed extraction schemas | Runtime nominal types, invariant mutable collections, typed throws | Domain/effect/refinement/security rules remain independent |
| Union meaning | Parse order affects branch selection | Set-like algebra with a parsing-order exception | Preserve explicit parser preference separately from normalized semantic unions |
| Execution | Generated host client + runtime | BexVM bytecode/async engine | Generate Elixir/Erlang and define OTP boundary semantics |

Evidence: [BAML documentation](../sources/baml-documentation.md), [pinned compiler](../sources/baml-canary-compiler.md). “TypeScript-like” describes familiarity; it is insufficient to settle any row.

See the [pinned BAML source walkthrough](compilers/baml.md) for Pratt/template parsing, actual hir_ty owner queries and shared-T stream defaults; [Rust walkthrough](compilers/rustc.md), [incrementality](compilers/incremental-compilation-and-source-identity.md) and [verification](testing/compiler-verification.md) deepen the mechanisms below.

## Small shared semantic core

**[Verified]** Rowan/rust-analyzer/Salsa demonstrate lossless syntax plus query-based semantics; rustc and BAML demonstrate different valid IR organizations. [Primary-source synthesis](../sources/compiler-tooling.md)

**[Proposal]** Begin with one Rust semantic library and thin CLI/LSP consumers. Keep grammar/trivia preservation separate from symbol/type/effect facts, and keep transport/filesystem watchers outside deterministic queries. Split crates only when ownership/build-time evidence warrants it. The specification permits combining listed modules. [Gaps](../planning/specification-gaps.md#blocking-language-and-abi-questions)

A minimal query graph can expose source/project/config inputs → lossless syntax and parse diagnostics → declarations/import interfaces → resolved function body → typed body/effect obligations → MIR → generated artifact/manifest. This is an ownership sketch, not a required pass order. Missing syntax yields recoverable error nodes; recovery types must not certify a security obligation or permit successful code generation.

Use separate semantic identity, source location and release identity:

- Semantic IDs identify declarations and locally owned expressions within a database revision. Neither byte offsets nor syntax-tree pointers are durable telemetry identities.
- Source maps relate syntax/desugared/generated locations to one or more authored spans, plus synthetic origins. Lowering must preserve those links through temporary variables, contracts and instrumentation.
- Published artifact identity includes compiler/language/ABI/source/schema fingerprints. A source-map match must be checked before runtime-to-source navigation; stale artifacts should show a mismatch.

Those are BEAML proposals. Rustc's item/body IDs and BAML's source-map separation are precedents, not proof that an arbitrary ID survives edits, renames or builds. [Compiler sources](../sources/compiler-tooling.md)

## Incrementality and determinism

**[Proposal]** Make compiler flags, dependencies, runtime/ABI descriptors, schema capabilities and reviewed foreign manifests explicit query inputs. Filesystem reads, environment lookup, clock access, solver nondeterminism and live LLM calls must not be hidden inside memoized semantic queries. Store provider fixtures as versioned test inputs.

Track declarations/interfaces separately from bodies and spans. A comment edit may require fresh diagnostic spans even if types stay equal; keeping spans inside semantic equality can defeat early cutoff. Body edits should invalidate actual dependents, while interface changes must invalidate callers and generated guards. BAML's compiler2 documents this separation; Salsa's red-green algorithm explains why it works. [BAML](../sources/baml-canary-compiler.md), [Salsa](https://salsa-rs.github.io/salsa/reference/algorithm.html)

Measure edits: whitespace before a declaration, local-expression change, exported signature change, import removal, ABI/schema-policy change, and malformed intermediate syntax. For each, compare incremental output with a fresh database and inspect recomputed-query counts. Equal answers alone detect stale caches; counts reveal ineffective granularity. Do not adopt latency targets as measured results.

## HIR/MIR choices and BEAM boundary

**[Proposal]** Preserve a source-friendly typed body for diagnostics; normalize only features that simplify semantic reasoning. A typed CFG MIR is justified by effect/control-flow/security obligations, but copying rustc's ownership machinery or BAML's VM model would introduce unrelated complexity. Define invariants for operation types, terminators, success/error edges, effect/capability calls, branch joins, partial streams and foreign boundaries before building optimization passes.

Every desugaring must preserve evaluation order, short-circuiting, error/cancellation behavior, label propagation and source origin. Generated Elixir/Erlang then needs a concrete policy for scalars/integers, nominal IDs, structs/maps, enums, closures, exceptions, process exits, cancellation and resource cleanup. BEAM compilation alone does not preserve the proposed semantics.

**[Requirement]** The owner adopted generated Elixir source as the initial backend, followed by the Elixir/OTP compiler and BEAM execution. [Decision source](../sources/syntax-spike-requirement.md). Direct bytecode emission is not an adopted later goal.

**[Proposal]** Emit deterministic readable source and a sidecar source map. Test generated compiler diagnostics and runtime stack failures against authored spans. Erlang annotations and Elixir parser/diagnostic metadata support attribution but do not replace that map; version-gated APIs require a pinned support matrix. [Backend sources](../sources/compiler-tooling.md#backend-locations-and-testing)

## LSP boundary

**[Proposal]** Pin a protocol/capability matrix; LSP 3.17 is a researched baseline, not an automatic product choice. Maintain versioned unsaved overlays and an immutable request snapshot. Convert UTF-8 byte offsets to negotiated LSP positions using an explicit line index; test non-BMP characters, combining characters, CRLF and EOF. Map external parser offsets deliberately rather than assuming all columns use one unit.

Drop or mark stale work instead of applying outdated edits. Publish an empty diagnostic set when fixed. Cross-file rename must use exact snapshot versions and non-overlapping edits, resolve semantic identity, and refuse dynamic/unknown syntax. Generated files should map navigation to authored source rather than offer edits to disposable output. [LSP contracts](../sources/compiler-tooling.md#editor-protocol-boundary)

HEEx/Elixir adapters need declared supported syntax and versioned official-parser behavior. Mapping extraction spans into the same database is an explicit boundary; regex event discovery cannot establish whole-language rename or security safety. The PDF requires that unsupported cases remain UNKNOWN. [Product contract](product-contract.md), [open UI questions](../planning/specification-gaps.md#ui-and-tooling-questions)

## Smallest reproducible vertical slice

**[Proposal]** This is the earlier, broader validation slice. The later [EXPERIMENT 0001](../../experiments/0001-syntax-to-beam/README.md) tests only a smaller exact-interface and nested-pattern subset. The complete sequence below remains unimplemented:

1. One record, enum/union, pure helper and prompt function with fixture response; one invalid-input and one invalid-type case.
2. Lossless parse, deterministic formatting, name/type diagnostic and one explicit effect boundary from the same semantic core.
3. Emit one backend module with input/output validation and source-map/ABI metadata; compile it under pinned Rust/Elixir/OTP toolchains and call it from a tiny Mix host.
4. Demonstrate valid call, rejected untrusted input before domain effects, provider-fixture parse failure, cancellation/cleanup, and runtime failure mapped to source.
5. Drive one unsaved edit through diagnostics/hover/definition with correct Unicode positions; prove fresh and incremental answers agree.
6. Save generated source, metadata and normalized diagnostics as reviewable fixtures. Record commands, versions, hardware and actual timing separately from specification gates.

This slice tests the compiler/runtime/editor seam. It does not need distributed workflows, a custom VM, full provider coverage, a solver, an Observatory UI or multiple backend emitters.

## Properties worth testing

**[Proposal]** Use independent laws/oracles rather than a second copy of each implementation:

| Surface | Property / evidence |
|---|---|
| Parser | Arbitrary bounded text never panics; token concatenation reproduces input including trivia; malformed fixtures recover without claiming validity |
| Formatter | Formatting is idempotent and preserves parsed semantics/comments under the declared grammar |
| Queries | Incremental output equals fresh output after generated edit sequences; interface changes invalidate dependents |
| Type/effect rules | Positive/negative normative examples, substitution laws where specified, foreign/unknown rejection; sampled tests remain TESTED rather than PROVED |
| MIR/backend | Checked MIR invariants; observable result/error/effect order agrees with a small normative evaluator on supported programs |
| Source mapping | Known authored diagnostics survive lowering; stale build IDs refuse mapping; Unicode offsets round-trip |
| ABI | Decode/encode round trips preserve allowed values; malformed/forged nominal or validation markers cannot bypass guards |
| Security | Join/order laws and pc-flow examples; unauthorized sinks reject even across error paths/foreign manifests |
| Streams | Token partition replay agrees on final result; no premature final-validation claim; cancellation and retry revision rules hold |

Bound generators by depth/size, preserve preconditions during shrinking, save minimized concrete regressions and seeds, and report reject/exhaustion counts. Proptest supports generation/shrinking/persistence; it does not decide BEAML's refined generators or prove semantic soundness. [Proptest sources](../sources/compiler-tooling.md#backend-locations-and-testing)

## Readiness questions

Before implementation tickets: which grammar and integer/null model is normative; which effect/error/cancellation rules cross BEAM; which ABI and parser versions are supported; which facts are inputs; which identities survive which edits/builds; which obligations may be statically proven versus enforced/tested/UNKNOWN; and which minimal pc-flow/security behavior is mandatory at P0? These are release-contract decisions. [Decision queue](../planning/specification-gaps.md)
