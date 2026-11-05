---
id: source-compiler-tooling
title: Compiler and tooling primary sources
kind: source
status: researched
updated: 2026-11-05
---

# Compiler and tooling primary sources

**[Verified]** Retrieved 2026-11-05. Versioned documentation and repository observations are recorded separately in [provenance](../../raw/research/compiler-tooling/provenance.json), with an [observation ledger](../../raw/research/compiler-tooling/research-record.md). No dependency was installed or selected.

## Lossless syntax and semantic queries

Rowan 0.17.0 provides generic lossless trees: immutable green nodes/tokens, construction and interning facilities. It supplies tree infrastructure, not BEAML grammar, type checking or incremental invalidation. [Published API](https://docs.rs/rowan/0.17.0/rowan/)

Rust-analyzer's architecture separates error-tolerant parsing/syntax from Salsa and LSP. Its parser returns a tree and errors, while syntax wrappers allow missing children. Analysis consumes in-memory source/project inputs; item summaries avoid global invalidation on body-only edits. These are useful architectural precedents rather than a library API commitment for BEAML. [Architecture](https://rust-analyzer.github.io/book/contributing/architecture.html)

Salsa derives memoized tracked computations from explicit inputs. Its model requires deterministic queries and outside mutation; dependencies are captured when query fields are read. Red-green validation can stop downstream recomputation when recomputed values compare unchanged. Query boundaries/equality therefore matter as much as choosing the framework. [Overview](https://salsa-rs.github.io/salsa/overview.html), [algorithm](https://salsa-rs.github.io/salsa/reference/algorithm.html)

The Rust compiler illustrates a different IR choice from BAML compiler2: rustc HIR is a desugared representation accessed by IDs, with body lookups exposing dependencies; MIR has explicit types and a control-flow graph of statements and terminators. Neither acronym specifies one universal design. [HIR](https://rustc-dev-guide.rust-lang.org/hir.html), [MIR](https://rustc-dev-guide.rust-lang.org/mir/index.html), [BAML comparison](baml-canary-compiler.md)

## Editor protocol boundary

LSP 3.17 position offsets depend on negotiated encoding; UTF-16 is the default required server support. Documents have versions; change events within notifications apply in order. A text-document edit refers to one document version and must not contain overlapping edits. These rules directly affect Unicode mapping, unsaved overlays and rename safety. [Position](https://github.com/microsoft/language-server-protocol/blob/440d8b03d784cf0bd3769b1abb33aacc24b586a6/_specifications/lsp/3.17/types/position.md), [changes](https://github.com/microsoft/language-server-protocol/blob/440d8b03d784cf0bd3769b1abb33aacc24b586a6/_specifications/lsp/3.17/textDocument/didChange.md), [edits](https://github.com/microsoft/language-server-protocol/blob/440d8b03d784cf0bd3769b1abb33aacc24b586a6/_specifications/lsp/3.17/types/textDocumentEdit.md)

Pushed diagnostics replace prior diagnostics for a document; empty sets clear old results. Document-version reporting is optional/capability-aware. Prepare-rename can refuse an invalid location, and rename can report failure. BEAML can use these protocol affordances to decline unsupported cross-language changes rather than fabricate safe edits. [Diagnostics](https://github.com/microsoft/language-server-protocol/blob/440d8b03d784cf0bd3769b1abb33aacc24b586a6/_specifications/lsp/3.17/language/publishDiagnostics.md), [rename](https://github.com/microsoft/language-server-protocol/blob/440d8b03d784cf0bd3769b1abb33aacc24b586a6/_specifications/lsp/3.17/language/rename.md)

## Backend locations and testing

Erlang's `erl_anno` carries source line/column/file/generated annotations. The observed OTP 29.1.2 page marks `set_end_location/2` as introduced in OTP 28.0. Generated annotation suppresses compiler warnings. These fields help backend attribution, but do not define a general many-to-many BEAML source-map protocol. [Annotations](https://www.erlang.org/doc/apps/stdlib/erl_anno.html)

Elixir's Code API compiles strings/files/quoted syntax and provides diagnostics, parser options and compilation tracers. Tracer events can run concurrently and future events may be added. It does not promise that arbitrary original-source spans survive all macro expansion and runtime stack frames. [Code](https://elixir.hexdocs.pm/Code.html)

Proptest generates cases and shrinks failures; its tutorial demonstrates Unicode parser panics and encourages saved regressions. Failure persistence assists reproduction, but generator/library changes can change produced cases, so a readable concrete regression remains valuable. These are testing tools, not a proof system. [Getting started](https://proptest-rs.github.io/proptest/proptest/getting-started.html), [persistence](https://proptest-rs.github.io/proptest/proptest/failure-persistence.html), [API 1.12.0](https://docs.rs/proptest/1.12.0/proptest/)

**[Proposal]** See [compiler/tooling synthesis](../concepts/compiler-and-tooling.md) for application to BEAML and evidence gates.
