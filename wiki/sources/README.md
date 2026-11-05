---
id: source-registry
status: evidence-index
updated: 2026-11-05
---

# Source registry

This registry indexes evidence, not implementation dependencies. All research was accessed 2026-11-05. Exact URLs, attribution, coverage and restrictions are recorded in each source page and linked raw provenance. **[Verified]** means read against upstream evidence, not executed in BEAML. Mutable documentation is date-pinned; version/commit-pinned sources are identified explicitly.

| Source page | Origin / version | Evidence role | Retained coverage / main limit |
|---|---|---|---|
| [Engineering specification](engineering-spec-v0.5.md) | Supplied PDF dated 2026-11-05; v0.3 baseline +v0.4/v0.5 appendices; SHA-256 in provenance | **[Requirement]** Intended BEAML product behavior | Full original + 14-page text extraction; design proposal, no implemented/measured/security-proof claim |
| [Karpathy LLM Wiki](karpathy-llm-wiki.md) | Andrej Karpathy Gist revision ac46de1ad27f92b28ac95459c782c07f6b8c964a | KB workflow inspiration | Selected researcher notes, not full text/comments; license not established |
| [Decision4](decision4.md) | Habitat Thinking 1.0.1, commit 5ccb19fc1fb8c6327d4edd8832550f7e8c40853e | Decision-consequence lens | Selected unchanged files; CC BY 4.0 text / MIT schema-examples; not inherited agent policy |
| [BAML established docs](baml-documentation.md) | BoundaryML mutable official docs | Typed prompts, SDK/schema/provider/testing/stream concepts | Selected attributed observations; not a single versioned language release |
| [BAML canary compiler](baml-canary-compiler.md) | BoundaryML commit a5db82f06c1da0dfac28e283a15d19d37a3f2cf2 | Compiler/type/runtime/query precedent | Selected source inspection, not executed; broader than established DSL docs; BexVM differs from OTP |
| [BAML reuse/license](baml-license.md) | Same pinned repository, Apache 2.0 root license | Reuse obligations and scope | Not full dependency/legal clearance; no BAML implementation copied |
| [Compiler/tooling](compiler-tooling.md) | Rowan 0.17.0, Proptest 1.12.0; LSP 3.17 pinned commit; rustc/rust-analyzer/Salsa docs | Lossless syntax, queries, IR, LSP and test precedents | Mixed pinned/mutable references; no dependencies selected or prototype executed |
| [BEAM/OTP/Phoenix](beam-otp-phoenix.md) | OTP 29.1.2, Elixir 1.20.x observed; LiveView source v1.2.13; Phoenix.HTML 4.3.0 | Runtime/Mix/HEEx feasibility | Selected source/docs, mixed cached doc versions; no compatibility tuple validated |
| [Information-flow security](information-flow-security.md) | Cornell Jif 3.3.0; Myers/Liskov; Hirsch/Cecchetti arXiv v2; EEF guidance | Label/pc/authority/effect and runtime-threat grounding | Selected docs and paper abstracts; no proof audit or BEAML theorem |
| [Observability/storage](observability-platforms.md) | OTel displayed spec 1.62.0 +mutable guides; Postgres 18; ClickHouse/AWS S3 docs | Context/privacy/queue/tenant/retention mechanisms | Selected paraphrases; no deployment benchmark, backend deletion test or signal package pin |

## Mechanism-level additions

| Source page | Source/version boundary | Local knowledge and limits |
|---|---|---|
| [Type-system foundations](type-system-foundations.md) | Milner 1978, author-hosted class/inference/refinement/effect papers, Software Foundations chapters, SMT-LIB 2.7 | Worked typing/inference/evidence/refinement/effect/state concepts; selected primary sections, not whole-paper proof audits. |
| [GHC compiler](ghc-compiler.md) | GHC 9.12.2 guide/source; mirror commit `383be28ffdddf65b57b7b111bfc89808b4229ebc` | Actual Tc.Module constraint/evidence/zonk, solver worklist/implication/evidence, demand/worker-wrapper, FC Core/Lint and STG/Cmm/update trace; historical FC/STG papers separately scoped. |
| [rustc internals](rustc-internals.md) | Rust 1.99.1 `58cf8f9c35b355199727627d07ae34a4e2846d67`; dev-guide `a29f8285990b8254783202aa0d86322eb21edf61` | Selected expansion/hygiene/type/goal/IR/query/borrow/const/backend source; no build or exhaustive unsafe/backend audit. |
| [BAML internals](baml-internals.md) | Same pinned BoundaryML commit as original canary note | Actual parser/type/MIR/emitter/runtime/stream source and fixtures; current code corrects stale architecture prose, no execution. |
| [BEAM VM internals](beam-vm-internals.md) | OTP 29.1.2 `d199a49a01a2079afb6f2c5c9ae047cd4555e68d` | Seven mechanism guides on compiler/JIT/terms/GC/processes/scheduling/native/distribution/storage/upgrades/inspection; explicit platform/historical limits. |
| [Typed BEAM languages](typed-beam-languages.md) | OTP 29.1.2 Dialyzer; pinned Gleam; Elixir 1.20.5 `4a28692668bef879029291b7ff329a84a1f933bb` | Success typing, ordinary-term generated ABI and gradual inference versus stronger BEAML validation/effect/security requirements. |
| [Phoenix/HEEx mechanisms](phoenix-heex-mechanisms.md) | LiveView 1.2.13 `d8252e1e21238e150e9e6b3d7285d4c060d28e6e`; Phoenix.HTML 4.3.0 `8cfd3e37ff9ef0924812a78cf6c9d27cdbd4e726` | Parser/slots/assign tracking/UTF coordinates/DOM forms/descriptor seam; internal APIs/macro execution/atom hazards explicit. |
| [Compiler verification](compiler-verification.md) | Rust/BAML source pins above; Proptest `70cf37d46b7d83393b6ed94c611f8c52209f585d`; LLVM/NIST selected docs | Independent test oracles, typed/trace shrinking/exhaustion, fuzzing, confidence/percentile methodology; none executed for BEAML. |

| [Domain contracts/evolution/architecture](domain-contracts-and-evolution.md) | Evans 2015/Eiffel contract tutorial; Ecto 3.14.3; Postgres 18; Akka 2.10.24; Avro 1.12.0; Protobuf/ArchUnit 1.5.1 docs | Aggregate/persistence scope, writer-reader versus semantic compatibility, graph/effect/taint evidence and waiver distinctions; no framework/runtime selected. |

The expanded [information-flow source](information-flow-security.md) and [Observatory source](observability-platforms.md) add Jif authority/pc/errors, candidate policy algebra/TCB, OTel 1.62.0 SDK and OTLP 1.11.1 transport, semantic conventions 1.45.0, W3C 2021 context, Postgres 18 audit durability and actual versioned storage deletion. Mutable operations docs remain date-scoped; a generic standard does not prove an Erlang package implements every signal feature.

## Corrections and historical evidence

Raw captures are immutable historical records. Read the maintained source/mechanism pages for the current interpretation:

- **BAML architecture prose versus code:** the conceptual TIR named in prose is implemented by `baml_compiler2_hir_ty`; actual MIR/emitter imports/infer_body establish the wiring. BexEngine's older epoch-GC description is stale relative to its heap-permit/parking/root-relocation implementation. [Corrected source trace](baml-internals.md), [compiler walkthrough](../concepts/compilers/baml.md).
- **BAML version tracks:** established SDK nullable partial types/Jinja/no-colon fields differ from pinned canary shared-T/schema-default stream behavior and colon/backtick interpolation. No single general compatibility contract follows. [Streaming comparison](../concepts/structured-output-and-streaming.md), [track distinction](../concepts/compilers/baml.md#three-distinctions-before-reuse).
- **OTP pipeline/history:** current tagged `compile.erl` uses integrated Core→SSA lowering; an old Kernel-related pass name/comment does not establish a separate current Kernel IR. Current binary structures also supersede the guide's acknowledged older layout description. [Compiler trace](../concepts/beam/execution-and-compilation.md), [memory trace](../concepts/beam/terms-memory-and-gc.md).
- **GHC provenance refinement:** initial selected notes could not resolve the release tag; a later immutable ref-resolution record establishes the full mirror commit. The maintained GHC pages use it, without claiming a local build/signature verification.

## Evidence refresh

**[Proposal]** Before implementing an adapter/dependency, pin the package/version tuple and any internal API source commit; add a new dated raw capture rather than replacing historical evidence. Read the relevant source note's coverage first. Add measured results separately from document claims. Follow [ingest/query/lint instructions](../../AGENTS.md); navigate via the [index](../index.md) and record changes in the [log](../log.md).

Registry provenance example: [supplied specification capture manifest](../../raw/specification/provenance.json). Each source row links its own full capture record.
