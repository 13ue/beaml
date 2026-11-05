---
id: concept-baml-source-walkthrough
title: BAML compiler, runtime schema and stream mechanisms
kind: synthesis
status: inspected-and-proposed
updated: 2026-11-05
---

# BAML compiler, runtime schema and stream mechanisms

**[Verified]** This is selected BoundaryML source inspection at `a5db82f06c1da0dfac28e283a15d19d37a3f2cf2`, retrieved 2026-11-05. Tests/fixtures are described as assertions, not observed passes. [Source map and limits](../../sources/baml-internals.md), [immutable record](../../../raw/research/baml-internals/record-2026-11-05.md)

## Three distinctions before reuse

| Track | What the evidence actually supports |
|---|---|
| Established documentation / engine | Schema-oriented functions, Jinja raw prompts, generated host clients/nullable partial types; not one release-pinned language spec |
| Pinned `baml_language` compiler2 / Bex runtime | General typed code, colon fields/config, backtick expression interpolation, ordinary synthesized companions, runtime nominal types and shared-T streams |
| BEAML proposal | Rust compiler to generated Elixir/Erlang, independent type/effect/refinement/security semantics and OTP runtime |

**[Verified]** Pinned `streaming_partial_parse.baml` concretely uses colon field/client/prompt syntax and `${...}` interpolation. This does not establish the whole accepted grammar; it establishes that “BAML syntax” must be version-scoped. [Fixture](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_tests/baml_src/ns_streaming_partial_parse/streaming_partial_parse.baml), [established-doc track](../../sources/baml-documentation.md)

## 1. Parse and normalize once

`baml_compiler_parser::parse_result` memoizes a green tree plus parse errors; `syntax_tree` exposes syntax. AST lowering synthesizes helper functions, so the type/MIR layers see ordinary functions instead of a separate LLM execution universe. `expand_companions` produces `@spec`, `@render_prompt`, `@build_request`, `@parse` and `@stream`; they share the parent's declaration identity/origin metadata but have distinct callable identities. [Parser](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler_parser/src/lib.rs), [companions](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_ast/src/companions.rs)

**[Inference]** This normalization is a good BEAML precedent: put prompt-specific sugar early, while retaining source origin and effects. It is not permission to hide external calls from effect/security checks merely because a wrapper is generated.

## Pratt expressions, template boundaries and formatting

**[Verified]** `parse_expr_bp(min_bp)` parses a prefix, then consumes infix/postfix forms until the next operator's left binding power is below the current minimum. The concrete table assigns plus `(22,23)`, multiplication `(24,25)` and assignment `(2,1)`. [Parser implementation and table](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler_parser/src/parser.rs#L6545)

A non-executed walkthrough: for `a + b * c`, outer plus recursively parses its right side at 23; multiply's left power 24 meets that threshold, giving `a + (b * c)`. For `a + b + c`, the second plus has 22 below the right-side threshold 23, so it returns to the outer loop, giving `(a + b) + c`. Assignment's lower right threshold allows right association. These numbers describe this pinned implementation, not BEAML's accepted precedence table.

Backtick parsing treats adjacent `${` as a hole; `$ {` remains text, and escapes/delimiters have explicit handling. `parse_backtick_interpolation` dispatches expression versus `if`/`for` template tags; expression holes reuse the host block-expression parser while surrounding text and whitespace stay in the parent literal. This is dedicated template structure plus host-expression reuse, not an assertion every interpolation language needs an independent expression grammar. CST token ranges preserve authored offsets; downstream synthesis must retain the hole/text origin. [Delimiter and dispatch logic](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler_parser/src/parser.rs#L2399), [hole body](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler_parser/src/parser.rs#L2621)

**[Proposal]** BEAML should publish operator associativity/precedence and hole terminator/escape/nesting/error rules, then test ambiguous `<` generics/comparison, braces inside quoted holes, escaped delimiters, missing closers, Unicode and newline recovery. A precise hole error should refer to authored bytes, not a reconstructed generated prompt.

**[Verified]** BAML `format_salsa` is syntax-only and uses shared lexer/parser/trivia classification. It returns parse errors rather than formatting an invalid tree, except a classified comment opt-out returns the original file. Scenario tests require idempotence and comment markers surviving exactly once. [Formatter entry](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_fmt/src/lib.rs), [scenario assertions](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_fmt/src/formatter_scenario_tests.rs)

**[Inference]** “Shares semantics” does not mean a formatter must run full type checking: it should reuse grammar/CST identity while semantic lints consume the common query DB. BEAML's malformed-editor behavior remains a decision; a formatter can refuse without losing bytes while the parser still serves diagnostics. Test comment attachment, CRLF, token/string contents and precedence-preserving parentheses separately from idempotence. [Supplemental capture](../../../raw/research/baml-internals/parser-formatter-2026-11-05.json)

## 2. Resolve names and infer a body through a semantic firewall

**[Verified]** Actual type code is `baml_compiler2_hir_ty`, not the `baml_compiler2_tir` crate named in architecture prose. Its inference entry dispatches per function, top-level let and parameter-default owner. Lambdas are inferred within the owner run. The opening migration commentary in hir_ty/lib.rs also lags concrete MIR/emitter imports; actual call sites are stronger evidence for current wiring. [Inference](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir_ty/src/infer.rs), [MIR consumer](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_mir/src/lower.rs), [emitter consumer](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_emit/src/lib.rs)

HIR's `file_semantic_index` is `no_eq` and refreshed on edits. Downstream `*_data` projections are span-free/equality-checked; `*_source_map` carries fresh spans. Ignoring spans only in equality would be wrong because cached diagnostics would retain old positions. The split lets unchanged semantics stop invalidation while locations update. [Firewall explanation and exports](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir/src/item_data.rs), [function projections](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir/src/item_data/functions.rs)

Inference combines synthesized and expected types, variable constraints, narrowing, candidate resolution and throws effects. The tracked function-body query seeds throws recursion with `never`; let cycles instead use an error seed and an in-flight guard. These are explicit cycle semantics, not one universal “cycles are okay” policy. [Owner queries/cycle handlers](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir_ty/src/infer.rs), [throws fixture](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_tests/src/type_spec/fixtures/throws_mutual_recursion_fixpoint.baml)

## 3. Type algebra and parsing preference are different

**[Verified]** Pinned semantics defines nominal concrete identity, transparent/equirecursive aliases, invariant classes/arrays/maps and set-like unions. Inference canonicalizes joins and checks obligations; the `invariant_generics_no_absorption` fixture protects the distinction between a union of different invariant instantiations and one widened instantiation. This is upstream semantics/fixture evidence, not BEAML's chosen variance. [Type-system reference](../../sources/baml-canary-compiler.md), [fixture](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_tests/src/type_spec/fixtures/invariant_generics_no_absorption.baml), [inference](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir_ty/src/infer.rs)

At the schema-aligned parsing boundary, union candidates are tried/coerced, a score-zero candidate can terminate search, a previous array-element hint can be tried first, and remaining candidates are scored. `FromLlmOutput` can parse a separate shape and refuse a value, triggering another candidate path. Runtime parsing is therefore not merely canonical set membership or strict JSON deserialization. [Union coercer](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_sap/src/deserializer/coercer/coerce_union.rs), [SAP interface](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/baml/ns_sap/sap.baml), [native conversion](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_vm/src/package_baml/sap.rs)

**[Proposal]** BEAML should specify parser policy separately from type algebra: coercion/repair provenance, ambiguous choice, ordering, branch revisions and user-defined shape validation. Ordinary type normalization must not accidentally reorder parser preference or silently change a model contract.

## 4. A checked revision reaches MIR and bytecode

**[Verified]** `CheckedWorld::check` refuses world errors, including errors with no primary span. It holds a shared DB reference so mutation cannot occur while that checked witness is used. Package cache/emitter/linker produce a program; the safe orchestration road gates emission on a checked revision, although lower-layer emitter functions remain callable APIs. [Program gate](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_db/src/program.rs), [diagnostic collection](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_db/src/check.rs)

`lower_function` consumes typed body/resolution data and checks indirect-call layouts. A user-error recovery artifact must not become a runnable placeholder; internal checker/lowering disagreement is an internal compile failure. MIR models blocks, locals, calls, unwind/handling and async terminators. Post-lowering cleanup removes dead blocks/stores/locals, propagates copies, folds constants/branches at O2, materializes operand prefixes at O1+, then orders blocks in RPO. [Lowering](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_mir/src/lower.rs), [passes](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_mir/src/optimize.rs)

Emission performs stackification and runtime type-template lowering. The debug/test verifier checks dense block indexing, redirect validity/convergence and unreachable defaults for exhaustive switches. Those checks catch internal drift; their configured profile and finite coverage must not be described as a formal preservation proof. [Emitter](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_emit/src/lib.rs), [verifier](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_emit/src/verifier.rs)

## 5. Runtime schema evidence is real data

**[Verified]** `FunctionSpec<Out>` retains callable identity, bound arguments, prompt callback, tools and default client. `call` delegates to the agent; `build_request` renders without invocation; `parse` invokes SAP. `output_type` reflects `Out` and validates output representability. [Standard-library spec](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/ai/spec.baml)

The VM SAP native extracts realized generic arguments; `build_model` walks reached class/enum/alias definitions and class instantiations; `CompiledSapModel` rejects unsupported targets/shapes and builds the parser model. Parsed values are allocated as the actual runtime declarations, preserving nominal identity rather than attaching an arbitrary class-name string afterward. Shape conversion may yield back into BAML code and propagate rejection/panic differently. [Native source](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_vm/src/package_baml/sap.rs), [model compilation](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_sap/src/lib.rs)

The compiler's `llm_output_findings` shares JSON-inhabitance analysis: known unrepresentable union branches/optional fields get findings, while generic/unknown/interface cases may defer checks to runtime. A compile-time warning is not a universal Schema witness, and a runtime parse failure is a permitted outcome. [Compiler findings](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir_ty/src/llm_output.rs)

**[Inference]** This supports BEAML's requirement that generic model calls need a reified schema. It does not settle monomorphization versus dictionary passing, witness ABI/versioning, refinements, or the distinct `Parsed`/`Validated` states proposed by the PDF.

## 6. Shared T does not mean a complete response

**[Verified]** Canary `Stream<T>.next` returns `T | Done`; `final` returns `T`. Both use one parse cache/model. Partial defaults can make a class runtime-representable before all text arrives; missing complete fields use a stricter rule. [Stream](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/ai/ns_stream/stream.baml), [default derivation](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_sap/src/sap_model/mod.rs)

| Case | Pinned source rule / fixture assertion |
|---|---|
| Incomplete string field | Can use empty string until text arrives |
| Nullable field | Can use null |
| Array/map | Can use empty container; omission can also default in complete object |
| Number/bool/nonnullable ambiguous union | No universal partial default; publication may wait |
| Completed required string missing | Error rather than treating prior temporary default as final input |
| Partial object with id=1 and name not received | Fixture expects id=1, name empty; completed id-only fixture errors |

Source: [partial_default/missing_default](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_sap/src/sap_model/mod.rs), [test_complete_missing_required_field_errors and test_partial_uses_default_where_complete_would_error](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_sap/src/tests/test_streaming.rs). These are inspected assertions, not reproduced results.

Stream `_next` accumulates text and skips `_NoYield`. EOF settles/caches a final parse; `final` can drain remaining chunks and reuse a cached value/error; cleanup releases resources and explicitly does not mean cancellation or successful parsing. Tests exercise fence/prose prefixes, malformed final replies, repeated final calls and spawned handoff. There is no general monotone immutable snapshot theorem in this evidence. [Lifecycle code](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/ai/ns_stream/stream.baml), [fixture assertions](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_tests/baml_src/ns_streaming_partial_parse/streaming_partial_parse.baml)

**[Proposal]** Preserve BEAML readiness/validation distinctions even if its runtime uses one underlying record shape. Missing, explicit null, generated default, incomplete text, validated final value and user-authorized effect are different facts. Defaults must not erase that distinction when the domain/schema requires it. [BEAML stream questions](../structured-output-and-streaming.md)

## 7. Errors/tasks/GC belong to the runtime contract

**[Verified]** Agent errors include typed provider/request/network/parse/tool outcomes and retry-safety classification; prompt callback failures wrap render errors. This is not a blanket proof of a capability/effect sandbox. Future natives use heap atomic settling and a cancellation token; runtime cancellation classification differs from ordinary user throws. [Error types](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/ai/ns_errors/errors.baml), [prompt/spec](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_builtins2/baml_std/ai/spec.baml), [future natives](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_vm/src/package_baml/future.rs), [project errors](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_project/src/lib.rs)

BexEngine drives VM execution until I/O and dispatches system operations. Actual source documents active heap permits, GC parking, root collection/forwarding and resumption; the older README's epoch description is stale at this pin. This shared-heap VM is materially different from BEAM process heaps/scheduling/supervision. [Engine implementation](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/bex_engine/src/lib.rs)

**[Unknown]** No complete race/GC/FFI/provider audit was done, and no claim task cancellation stops every foreign operation. BEAML's backend must define these outcomes rather than infer them from “green threads” or OTP support.
