# Compiler/tooling research record

Retrieved 2026-11-05. External facts from primary sources; no code, package selection, installation or benchmark performed.

| Primary source | Observation used |
|---|---|
| https://docs.rs/rowan/0.17.0/rowan/ | Generic lossless syntax-tree library; immutable green nodes/tokens, builder and node interner |
| https://rust-analyzer.github.io/book/contributing/architecture.html | Error-tolerant parser; syntax independent from Salsa/LSP; semantic item summaries stable under body edits; in-memory analysis inputs |
| https://salsa-rs.github.io/salsa/overview.html | Deterministic input/tracked-query database and field dependency tracking |
| https://salsa-rs.github.io/salsa/reference/algorithm.html | Revision/dependency checks, red-green/backdating and durability |
| https://rustc-dev-guide.rust-lang.org/hir.html | Desugared HIR and item/body IDs accessed through dependency-recording lookups |
| https://rustc-dev-guide.rust-lang.org/mir/index.html | Fully typed CFG MIR, explicit operations, statements/terminators |
| https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/ | Published protocol version; website extraction navigation only, so raw sections used |
| Microsoft repository `_specifications/lsp/3.17/types/position.md` | Zero-based positions, negotiated encoding, UTF-16 default |
| Same repository `types/textDocumentEdit.md`, `types/versionedTextDocumentIdentifier.md` | Non-overlapping edits and versioned document identity |
| Same repository `textDocument/didChange.md` | Ordered incremental changes and post-change versions |
| Same repository `language/publishDiagnostics.md`, `language/rename.md` | Diagnostic replacement/clearing, optional versions, prepare-rename refusal |
| https://proptest-rs.github.io/proptest/proptest/getting-started.html | Generation/shrinking and UTF-8 parser bug example; independent properties rather than duplicate implementation |
| https://proptest-rs.github.io/proptest/proptest/failure-persistence.html | Persist regression seeds and understand limitations of exact future reproduction |
| https://docs.rs/proptest/1.12.0/proptest/ | Published API/version observation |
| https://www.erlang.org/doc/apps/stdlib/erl_anno.html | Compiler annotations for location/file/generated/end location, version-gated APIs |
| https://elixir.hexdocs.pm/Code.html | Compile source/quoted code; diagnostic/parser metadata and compilation tracer boundaries |

Exact repository HEADs and LSP section hashes are in provenance.json. BAML compiler evidence is separately pinned in ../baml/provenance.json. Full third-party sources were not copied into the repository.

## Research interpretation

A Rust semantic core with lossless syntax and an incremental database is well supported by existing implementations. It still needs a BEAML grammar/type/effect contract, dependency granularity, cancellation/revision discipline, generated-source mapping and a versioned BEAM boundary. Library existence proves neither BEAML latency targets nor soundness. A deterministic vertical slice is the next evidence-producing artifact; it is a proposal, not work performed in this ingestion.
