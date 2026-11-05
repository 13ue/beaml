---
id: concept-incremental-source-identity
title: Incremental compilation and source identity
kind: synthesis
status: inspected-and-proposed
updated: 2026-11-05
---

# Incremental compilation and source identity

**[Requirement]** BEAML queries must be deterministic with tracked dependencies/cycle diagnostics; cache keys include compiler/features/schema/import interfaces, and prompt-only changes should spare unrelated typing. Stable semantic IDs and source maps must span lowering, editing and runtime metadata. These are desired contracts, not implemented facts. [Spec p.2 §4; pp.3,5,9 §§5,10,25](../../sources/engineering-spec-v0.5.md)

## Three mechanisms often called “incremental”

| Mechanism | What can be reused | Distinct obligation |
|---|---|---|
| Region reparse | Unchanged syntax subtrees within one file | Correct lexical/context boundary and recovery behavior |
| Semantic memoization | Unchanged query answers and dependent computations | Complete explicit inputs, equality and dependency recording |
| Persistent artifact reuse | Prior-session query/object/generated packages | Stable identity, version/fingerprint/serialization compatibility and stale-file removal |

**[Inference]** Implementing one does not establish the others. A Salsa parse query can reparse the full file and still memoize type results; a lossless tree does not prove minimal invalidation; a content hash does not explain dependency granularity. [Salsa model](https://salsa-rs.github.io/salsa/overview.html), [rustc persistence](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/queries/incremental-compilation-in-detail.md), [BAML parser](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler_parser/src/lib.rs)

## Red-green validation and read order

**[Verified]** rustc records query reads as dependencies. A previous result can be reused when dependencies are green; if an input may have changed, the provider can rerun and compare the result fingerprint, stopping propagation if unchanged. Actual `try_mark_previous_green` traverses prior read edges, forces an unproven dependency and inspects its resulting color. Query control flow matters: after an earlier dependency changes, a later old dependency might no longer be relevant, so do not assume the old edge set is an unordered truth about the new run. [Source algorithm](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_middle/src/dep_graph/graph.rs), [guide](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/queries/incremental-compilation-in-detail.md)

Salsa similarly records field/query dependencies and uses unchanged results for early cutoff. It requires deterministic computation from explicit inputs. Equality precision is a design decision: including all source bytes/locations can cause broad invalidation; dropping semantically relevant data can return stale answers. [Overview](https://salsa-rs.github.io/salsa/overview.html), [red-green/backdating](https://salsa-rs.github.io/salsa/reference/algorithm.html)

**[Proposal]** Make file overlays, imports, feature flags, compiler/language version, schema/effect/foreign capability manifests and policies explicit inputs. A live LLM call, filesystem lookup, clock/random value or hidden environment read is not a valid deterministic semantic-query dependency. Keep fixture execution and effectful probes outside the memoized compiler facts.

## Semantic data must not retain stale locations

**[Verified]** BAML's HIR `item_data` firewall separates span-free `*_data` from `*_source_map`. Its upstream semantic index reports changed after each edit, while projections compare cheap semantic results. Body inference uses location-free inputs and equality; diagnostic rendering resolves current maps. It explicitly warns that ignoring spans in equality while retaining them in cached results leaves stale locations. [Firewall](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir/src/item_data.rs), [owner inference](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir_ty/src/infer.rs)

**[Proposal]** BEAML diagnostic facts should store code, semantic owner/local origin, expected/actual types and related-origin references; render byte spans from the revision's source map. Split authored and synthetic origins so a moved definition updates navigation even if its type is unchanged. This requires tests, not a comment claiming stable IDs.

## Stable for which lifetime?

**[Verified]** rustc's persistent system cannot serialize session-local numeric DefIds as durable identity. The guide uses definition-path hashing/stable hashing and remaps identities on loading; not every query result is serialized because I/O/decoding costs can outweigh recomputation. Query result reuse, object reuse and diagnostic side-effect replay are separate mechanisms. Source includes diagnostic recording/replay beside dependency colors. [Persistence guide](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/queries/incremental-compilation-in-detail.md), [diagnostic side-effect methods](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_middle/src/dep_graph/graph.rs)

| Identity | BEAML proposed lifetime | Avoid |
|---|---|---|
| File/document revision | One unsaved-overlay snapshot | Mixing stale parse text with new source locations |
| Definition/body-local ID | Semantic DB and explicitly defined matching rules across edits | Assuming a byte offset, name or insertion index is globally durable |
| Source-map/artifact ID | One compiler/version/source/ABI build | Mapping old runtime events onto a different generated program |
| Operation/release identity | Published contract/version with declared migration | Hashing sensitive payloads or customer data into a supposedly harmless stable ID |

**[Proposal]** Define rename/move/delete/recreate behavior and collision handling for each identity. A content hash can safely invalidate conservatively without being a human-meaningful semantic ID. BAML's `project_source_content_hash` intentionally changes on project-byte/compiler-version changes; it serves content identity, not proof that definitions retain identities across edits. [Emitter hash](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_emit/src/lib.rs), [spec privacy boundary](../../sources/engineering-spec-v0.5.md)

## Cycles and failure states

**[Verified]** BAML infers recursive throws with an explicit bottom seed but handles let-initializer inference cycles with error-typed recovery. Rust queries/trait goals likewise have domain-specific cycle/overflow handling. Recursive types, recursive trait evidence, cyclic packages and recursive value initialization are different relations. [BAML inference](https://github.com/BoundaryML/baml/blob/a5db82f06c1da0dfac28e283a15d19d37a3f2cf2/baml_language/crates/baml_compiler2_hir_ty/src/infer.rs), [Rust solver invariants](https://github.com/rust-lang/rustc-dev-guide/blob/a29f8285990b8254783202aa0d86322eb21edf61/src/solve/invariants.md)

**[Proposal]** BEAML should define legal recursion/fixpoint order and failure policy per query family. Errors/UNKNOWN/timeouts must be cached with their actual assumptions and must not turn into successful validation. Cache invalidation must include the solver/checker version and budgets when they affect an answer.

## The source-to-BEAM-to-editor boundary

**[Verified]** Rust SourceMap handles byte positions/files/snippets; hygiene adds expansion provenance. Erlang annotations and Elixir metadata help backend attribution but do not define a many-to-many cross-language source map. LSP positions use negotiated encoding and edits target document versions. [Rust locations](https://github.com/rust-lang/rust/blob/58cf8f9c35b355199727627d07ae34a4e2846d67/compiler/rustc_span/src/source_map.rs), [LSP/backend source note](../../sources/compiler-tooling.md)

**[Proposal]** Store an explicit authored→HIR/MIR→generated mapping, including synthetic nodes and one-to-many expansions. Runtime events carry a source-map/build identity checked before navigation. Convert each parser's offset unit to UTF-8 bytes, then to negotiated LSP units; test non-BMP/combining characters, CRLF, heredoc indentation and EOF. Refuse stale rename edits and unsupported dynamic HEEx transformations.

## Evidence matrix before latency claims

**[Proposal]** For each edit, compare incremental normalized diagnostics/types/MIR/artifacts with a fresh DB; record recomputed queries and source-map correctness separately:

| Edit | Expected distinction to test |
|---|---|
| Whitespace/comment before a declaration | Fresh spans, same semantic types |
| Prompt literal body | Prompt preview/artifact changes; unrelated type facts reusable |
| Local expression/type error | Owner and actual dependents update; recovered IDE facts never permit emit |
| Exported signature/schema | Callers/guards/schema fingerprints invalidate |
| Policy/foreign manifest/compiler flag | Relevant effect/security/artifact results invalidate |
| File delete/import rename | No stale symbol/reference/generated module remains |
| Cancelled/out-of-order overlay request | No stale diagnostics or edits publish as current |
| Cold restart/version mismatch | Persistent cache accepted only under compatible identities; fallback fresh result agrees |

This is a proposed test matrix, not a measured invalidation guarantee. See [verification](../testing/compiler-verification.md).
