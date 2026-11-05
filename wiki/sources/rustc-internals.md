---
id: source-rustc-internals
title: Rust compiler internals
kind: source
status: inspected-not-executed
updated: 2026-11-05
---

# Rust compiler internals

**[Verified]** Publisher: Rust Project. Rust 1.99.1 source pin `58cf8f9c35b355199727627d07ae34a4e2846d67` (2026-10-13); compiler-guide pin `a29f8285990b8254783202aa0d86322eb21edf61` (2026-11-02); retrieved 2026-11-05. Selected module/chapter inspection, not a build/full correctness audit. [Raw observations](../../raw/research/rustc-internals/record-2026-11-05.md), [file provenance](../../raw/research/rustc-internals/provenance-2026-11-05.json). Upstream copyrights/licenses remain with publishers.

## Concrete source map

Paths are within the pinned Rust repository. Symbols are reading entry points, not stable public APIs.

| Mechanism | Source / symbol | Checked behavior |
|---|---|---|
| Front end | [passes.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_interface/src/passes.rs), [parser/mod.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_parse/src/parser/mod.rs) | Parse/configure/expansion orchestration; recursive-descent AST parsing |
| Macro integration | [expand.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_expand/src/expand.rs), `fully_expand_fragment` | Expansion queue, AST integration and macro/import resolution |
| Name context | [resolve/lib.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_resolve/src/lib.rs), [hygiene.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_span/src/hygiene.rs) | Resolution state and SyntaxContext/ExpnId provenance |
| HIR | [ast_lowering/lib.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_ast_lowering/src/lib.rs) | Expanded AST lowering/desugaring and IDs |
| Body typing | [hir_typeck/lib.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_hir_typeck/src/lib.rs), `typeck_root`, `typeck_with_inspect` | Body-owner results, expected types, coercion/writeback and obligations |
| Inference | [infer/mod.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_infer/src/infer/mod.rs) | InferCtxt, variable tables, snapshot/probe context |
| Trait engines | [select/mod.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_trait_selection/src/traits/select/mod.rs), [fulfill.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_trait_selection/src/traits/fulfill.rs), [next solve/mod.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_next_trait_solver/src/solve/mod.rs) | Classic selection/fulfillment coexist with next solver; no universal enabled mode inferred |
| Typed bodies / MIR | [mir_build/lib.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_mir_build/src/lib.rs), `provide` | thir_body, match/unsafety checks and build hook |
| Borrow/const/transforms | [borrowck/lib.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_borrowck/src/lib.rs), [eval_queries.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_const_eval/src/const_eval/eval_queries.rs), [mir_transform/lib.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_mir_transform/src/lib.rs) | Borrow check, const queries and staged MIR passes |
| Backend | [collector.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_monomorphize/src/collector.rs), [codegen_ssa/base.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_codegen_ssa/src/base.rs) | Reachable monomorphic items and backend orchestration |
| Incremental engine | [dep_graph/graph.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_middle/src/dep_graph/graph.rs), `try_mark_green`, `try_mark_previous_green`, `hash_result` | Dependencies, fingerprints, previous graph and diagnostic side effects |
| Locations | [source_map.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_span/src/source_map.rs), `SourceMap` | File/byte-position/line/snippet lookup and path remapping |
| Tests/invariants | [validate.rs](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_mir_transform/src/validate.rs), [MIR-opt README](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/tests/mir-opt/README.md), [incremental span test](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/tests/incremental/spans_in_type_debuginfo.rs) | Phase-sensitive CFG/types/debuginfo, pass dumps/diffs and revision regression |

## Guide cross-checks and limits

Pinned chapters explain [macro expansion](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/macro-expansion.md), [inference](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/type-inference.md), [THIR](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/thir.md), [borrow checking](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/borrow-check.md), [queries](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/query.md), [incremental persistence](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/queries/incremental-compilation-in-detail.md), [trait goals](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/solve/trait-solving.md) and [canonicalization](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/solve/canonicalization.md). Guide chapters have their own dated sections and may be ahead of the release source.

**[Unknown]** No complete pass ordering for every flag/target, unsafe/LLVM proof audit, IDE responsiveness guarantee or BEAML measurement. **[Inference]** Transfer mechanisms/invariants, not rustc's whole crate layout/ownership system. See [walkthrough](../concepts/compilers/rustc.md) and [incremental/source identity](../concepts/compilers/incremental-compilation-and-source-identity.md).
