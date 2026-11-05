---
id: concept-rustc-walkthrough
title: How rustc turns source into checked executable code
kind: synthesis
status: inspected-and-proposed
updated: 2026-11-05
---

# How rustc turns source into checked executable code

**[Verified]** This is an upstream mechanism walkthrough, not BEAML's chosen architecture. Source pin: Rust 1.99.1; guide pin/date and selected coverage are in [source note](../../sources/rustc-internals.md). No examples were compiled. **[Requirement]** BEAML's proposed lossless CST, shared semantic queries, typed MIR and semantics-preserving BEAM backend are distinct obligations. [Spec pp.1–3 §§2–5](../../sources/engineering-spec-v0.5.md)

## A useful pipeline, without pretending it is one linear loop

```text
source → tokens → AST ↔ macro/import expansion and resolution
       → resolved/desugared HIR → body inference + obligations
       → typed body (THIR) → analysis MIR
       → borrow/const checks and staged MIR transformations
       → reachable monomorphic items → codegen units → backend/link
```

**[Verified]** Queries drive much of this work on demand; bodies and definitions are not necessarily processed in textual order. Macro expansion and resolution interact, const evaluation may demand MIR, and not every check-only invocation reaches backend generation. [Driver wiring](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_interface/src/passes.rs), [query declarations](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_middle/src/query/mod.rs), [guide query model](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/query.md)

## 1. Parsing, macros and name provenance

**[Verified]** `rustc_lexer` supplies low-level tokens; `rustc_parse` performs recursive-descent AST parsing. AST nodes retain spans/token information needed by compiler/procedural macros, but this is not the same data structure as Rowan's lossless green/red CST. BEAML still needs trivia preservation and incomplete-code recovery explicitly. [Parser](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_parse/src/parser/mod.rs), [guide overview](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/overview.md), [lossless tooling comparison](../compiler-and-tooling.md)

`MacroExpander::fully_expand_fragment` maintains unresolved invocations, resolves imports/macro names sufficiently to expand one, parses/integrates its output and discovers more invocations. Failure to make progress becomes a diagnostic; recovery can insert error expressions to report later problems. Ordinary name resolution is not simply finished before expansion starts. [Implementation](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_expand/src/expand.rs), [expansion algorithm](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/macro-expansion.md)

Identifiers carry a syntax context as well as spelling and position. `ExpnId` and `SyntaxContext` track expansion/hygiene provenance; they let names introduced at different expansion contexts resolve differently even when their text matches. Module/type/value/macro resolution information resides in `rustc_resolve`. A generated name's source span alone cannot supply hygiene. [Hygiene structures](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_span/src/hygiene.rs), [resolver](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_resolve/src/lib.rs)

**[Inference]** BEAML need not copy a macro system to borrow the lesson: synthesized prompt helpers, validators and instrumentation need collision-free semantic identities and an origin chain. A diagnostic should distinguish authored expression, generated wrapper and foreign expansion. This cannot be reconstructed reliably from generated line numbers later.

## 2. HIR, owner bodies and type inference

**[Verified]** AST lowering creates HIR after expansion/resolution and desugars source constructs. HIR item/body IDs permit looking up one body without eagerly reading every sibling. That access boundary is important for recording dependencies. HIR syntax types describe what the user wrote; internal `Ty` values represent interpreted types. [Lowering source](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_ast_lowering/src/lib.rs), [HIR guide](https://rustc-dev-guide.rust-lang.org/hir.html)

`rustc_hir_typeck::typeck_root`/`typeck_with_inspect` compute owner-body typing results, with `FnCtxt`, expression checking, expected types, coercions, local inference and writeback. Closures share their enclosing type-checking root. `type_of(def_id)` is an item-type query; it is not a universal per-expression IDE inference interface. [Body checker](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_hir_typeck/src/lib.rs)

`InferCtxt` contains unification state for inference variables. Relating types may constrain variables and emit more trait/subtyping obligations rather than settle everything immediately. Probe/snapshot operations can try a candidate and roll back, avoiding speculative constraints contaminating later candidates. Region constraints are collected for later reasoning, so an early compatibility probe is not a finished lifetime proof. [Inference source](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_infer/src/infer/mod.rs), [guide mechanisms](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/type-inference.md)

**[Inference]** For BEAML, a useful distinction is “unsolved metavariable”, “user-visible unknown/foreign boundary” and “error recovery sentinel”. Treating all three as one permissive top type risks accepting broken programs. An editor may display partial inference results while code generation and security claims remain blocked.

## 3. Trait obligations are not ordinary name lookup

**[Verified]** Classic trait selection/fulfillment lives in `rustc_trait_selection`; the next solver has its own `rustc_next_trait_solver` implementation. The captured next-solver module names routing controls and labels itself WIP, so this note does not claim all default compilation uses it. [Classic selection](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_trait_selection/src/traits/select/mod.rs), [fulfillment](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_trait_selection/src/traits/fulfill.rs), [next solver](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_next_trait_solver/src/solve/mod.rs)

The guide's goal model asks whether a predicate holds under a parameter environment. Candidate exploration can add nested goals and constraints. Canonicalization replaces local inference variables with a reusable canonical form, then a response must be instantiated back into the caller. Ambiguity/overflow are distinct from a demonstrated negative result; recursive goals and cache/provisional results need explicit rules. The next source has a bounded fixpoint step limit, showing termination/overflow policy is part of the mechanism. [Goal model](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/solve/trait-solving.md), [canonicalization](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/solve/canonicalization.md), [invariants](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/solve/invariants.md), [source limit](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_next_trait_solver/src/solve/mod.rs)

**[Proposal]** BEAML's first coherent non-overlapping traits should state candidate applicability, ambiguity, recursion/normalization limits and diagnostics. Do not copy the full Rust solver before BEAML's trait contract requires it. Generic Schema witnesses must be carried through whichever monomorphized/dictionary ABI is chosen; an inferred compile-time bound is not itself a runtime descriptor.

## 4. THIR makes implicit operations explicit

**[Verified]** THIR is a typed executable-body representation built after type checking. It resolves implicit adjustments, method/operator calls and destruction scopes into more explicit operations. It omits declarations such as whole struct/trait definitions and is kept only as long as needed to limit memory. `rustc_mir_build::provide` registers `thir_body`, pattern/unsafety checks and MIR construction. [THIR guide](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/thir.md), [provider source](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_mir_build/src/lib.rs)

MIR is a typed CFG: basic blocks contain statements and terminators; nested expression evaluation is flattened into locals/operands. Calls/unwind/cleanup edges make control flow visible. MIR phases have different invariants; `Validator` checks CFG, types and debug records and is aware of the current phase. [MIR guide](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/mir/index.md), [pass schedule](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_mir_transform/src/lib.rs), [validator](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_mir_transform/src/validate.rs)

**[Proposal]** BEAML's typed MIR should likewise expose success/error/cancellation, effects, validation and security-release operations. It need not inherit Rust moves/drops. A lowering that preserves numeric results but moves a sink before validation is still incorrect. Keep evaluation order and source/security metadata in the observable-semantics contract.

## 5. Borrow checking, const evaluation and code generation

**[Verified]** MIR borrow checking uses move/dataflow facts, a MIR type check to collect region constraints, region inference over CFG points, and a final access walk. It enforces Rust-specific initialization/move/borrow rules; it does not automatically prove an arbitrary effect system or BEAM resource protocol. [Borrow checker source](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_borrowck/src/lib.rs), [phases](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/borrow-check.md)

Const evaluation is a separate MIR-interpreter/query path, with explicit limits/errors; ordinary code is not generally executed at compile time. The monomorphization collector finds concrete reachable instances/statics, and codegen partitions/lowers them through a backend. The common LLVM route is a backend choice; writing the frontend in Rust does not force BEAML to target LLVM or use rustc internals. [Const queries](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_const_eval/src/const_eval/eval_queries.rs), [collector](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_monomorphize/src/collector.rs), [backend](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_codegen_ssa/src/base.rs)

**[Unknown]** No BEAML schema generic strategy, arbitrary refinement solver, ownership model or const evaluator is selected here. For restricted natural const expressions and interval refinements, publish a bounded semantics before considering a general interpreter/SMT layer.

## 6. What is reusable for an IDE, and what is not promised

**[Verified]** Compiler recovery types/error nodes allow multiple diagnostics, but that does not establish latency/cancellation/stale-edit behavior for interactive incomplete projects. Rust-analyzer uses its own error-tolerant syntax and semantic architecture rather than treating a full rustc invocation as an LSP API. [Parser/typing sources above](../../sources/rustc-internals.md), [rust-analyzer architecture](https://rust-analyzer.github.io/book/contributing/architecture.html)

**[Proposal]** BEAML should share language rules between build and IDE consumers while providing recoverable partial facts and revisioned snapshots. A build must reject errors even if an editor can hover nearby. See [query/identity invariants](incremental-compilation-and-source-identity.md) and [verification strategy](../testing/compiler-verification.md).
