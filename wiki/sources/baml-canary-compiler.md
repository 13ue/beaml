---
id: source-baml-canary-compiler
title: "BAML: pinned canary language and compiler"
kind: source
status: researched
updated: 2026-11-05
---

# BAML: pinned canary language and compiler

Status: upstream implementation/design evidence, not chosen BEAML semantics. Retrieved 2026-11-05. Repository `BoundaryML/baml`, branch `canary`, commit `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`, committer timestamp `2026-11-05T05:58:34Z`. [Machine-readable provenance](../../raw/research/baml/provenance.json)

**[Verified]** Source observations below were checked directly, not tested in BEAML. Publisher: BoundaryML. Upstream source/code remains subject to its own license; these are attributed research summaries.

## Language semantics and their evidence

The pinned [type-system document](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/TYPE_SYSTEM.md) describes a set-theoretic system: subtyping is subset inclusion; concrete classes/enums have nominal identity; aliases are transparent; `unknown` is top and `never` bottom. Optional `T?` means `T | null`. Runtime values retain concrete type information. Classes, arrays and maps are invariant in their generic parameters; functions are contravariant in inputs and covariant in returns/errors. This is substantially more than TypeScript surface resemblance.

Function signatures include an error type. Exhaustive `throws T` is checked; omitted throws can be inferred for bodies, while interface/native boundaries require explicit clauses. A partial clause (`throws AppError | _`) retains named errors and infers the rest. `throws never` excludes typed throws but still permits panic. Interfaces use trait-like implementation/coherence rules rather than class inheritance. These are documented semantics at the pinned commit, not an independently reproduced conformance report. [Functions, interfaces and subtyping](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/TYPE_SYSTEM.md)

A subtle split matters for BEAML: type-algebra unions are treated set-theoretically, but the type document explicitly retains declaration-order significance at the LLM parsing boundary. Canonicalizing a union must therefore not silently discard parser preference. [Subtyping cases](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/TYPE_SYSTEM.md#baml-subtyping-cases)

## Compiler and runtime

Compiler2's [architecture reference](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/ARCHITECTURE.md) specifies lossless, error-tolerant green/red CST; CST→AST desugaring; HIR names/scopes and a conceptual typed query layer over AST; AST→MIR control-flow lowering; MIR→BexVM bytecode. HIR/TIR are not successive rewritten syntax trees in this architecture. Salsa tracked queries form the incremental database. Per-item semantic data is separated from source maps so offset-only edits can stop invalidation; lambda bodies remain tied to their enclosing function's body query.

LLM functions become regular functions plus metadata/companions during AST lowering. Client blocks similarly desugar into ordinary bindings/constructors. This keeps domain syntax from infecting lower compiler stages. [AST and incrementality sections](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/ARCHITECTURE.md)

The [current engine source](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_engine/src/lib.rs) describes VM/I/O mediation and active heap permits with semaphore parking, root collection and relocation. The older engine README's epoch-GC description lags this implementation. This is not OTP scheduling, process isolation or supervision. A BEAM backend must define its own runtime contract. [Source-level correction/trace](baml-internals.md)

The [FunctionSpec/streaming design note](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/FUNCTION_SPEC_STREAMING_DESIGN.md) claims implemented support for exact function companions (`@spec`, `@stream`, `@render_prompt`, `@build_request`, `@parse`), nominal runtime values across FFI, cancellation propagation and stream capability lifetimes. Treat it as a pinned design/status record; no SDK conformance tests were run here.

**[Verified]** Source inspection corrects the architecture document's concrete names: actual type inference lives in `baml_compiler2_hir_ty::infer::infer_body`, with tracked per-owner queries, rather than a crate named `baml_compiler2_tir` or a universal `infer_scope_types`. Pinned fixtures use colon fields/config and backtick interpolation; canary streams share T with schema defaults. Earlier raw research is preserved; see [deep source trace](baml-internals.md).

## Version and adoption caveat

GitHub's latest-release API returned `baml-language-0.23.1-nightly.20261104.a` at retrieval, targeting `c83cef10dd18741b47c5a3fb5d2334d076ff6e17`, published `2026-11-05T09:07:44Z`, with `prerelease=false`. The nightly name and flag are both preserved as observations. Neither establishes stable compatibility. [Release](https://github.com/BoundaryML/baml/releases/tag/baml-language-0.23.1-nightly.20261104.a)

**[Proposal]** BEAML should choose a compatibility target explicitly: inspired syntax, DSL interchange, parser behavior, or full runtime compatibility. The inspected code supports architectural comparison; it does not make any of those choices for this project.
