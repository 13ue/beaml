---
id: source-registry
status: evidence-index
updated: 2026-11-06
---

# Source registry

This registry indexes evidence, not implementation dependencies. Most research was accessed 2026-11-05; later access dates are on each source page. Exact URLs, attribution, coverage and restrictions are recorded in each source page and linked raw provenance. **[Verified]** means read against upstream evidence, not executed in BEAML. Mutable documentation is date-pinned; version/commit-pinned sources are identified explicitly.

| Source page | Origin / version | Evidence role | Retained coverage / main limit |
|---|---|---|---|
| [Engineering specification](engineering-spec-v0.5.md) | Supplied PDF dated 2026-11-05; v0.3 baseline +v0.4/v0.5 appendices; SHA-256 in provenance | **[Requirement]** Intended BEAML product behavior | Full original + 14-page text extraction; design proposal, no implemented/measured/security-proof claim |
| [Karpathy LLM Wiki](karpathy-llm-wiki.md) | Andrej Karpathy Gist revision ac46de1ad27f92b28ac95459c782c07f6b8c964a | KB workflow inspiration | Selected researcher notes, not full text/comments; license not established |
| [Decision4](decision4.md) | Habitat Thinking 1.0.1, commit 5ccb19fc1fb8c6327d4edd8832550f7e8c40853e | Decision-consequence lens | Selected unchanged files; CC BY 4.0 text / MIT schema-examples; not inherited agent policy |
| [BAML established docs](baml-documentation.md) | BoundaryML mutable official docs (BAML v0, "legacy DSL") | Typed prompts, SDK/schema/provider/testing/stream concepts | Selected attributed observations; not a single versioned language release |
| [BAML canary compiler](baml-canary-compiler.md) | BoundaryML commit a5db82f06c1da0dfac28e283a15d19d37a3f2cf2 | Compiler/type/runtime/query precedent | Selected source inspection, not executed; broader than established DSL docs; BexVM differs from OTP |
| [BAML v1](baml-v1.md) | BoundaryML commit 989676dd5169497c0d2a8d8e1d10914e987ae262; release `baml-language-0.25.1`; accessed 2026-11-06 | v1 language, stdlib, runtime, hosts, tooling, observability, release status | Selected code read and release/web observations, not executed; no 1.0; PR descriptions only |
| [BAML reuse/license](baml-license.md) | Same pinned repository, Apache 2.0 root license | Reuse obligations and scope | Not full dependency/legal clearance; no BAML implementation copied |
| [Compiler/tooling](compiler-tooling.md) | Rowan 0.17.0, Proptest 1.12.0; LSP 3.17 pinned commit; rustc/rust-analyzer/Salsa docs | Lossless syntax, queries, IR, LSP and test precedents | Mixed pinned/mutable references; no dependencies selected or prototype executed |
| [BEAM/OTP/Phoenix](beam-otp-phoenix.md) | OTP 29.1.2, Elixir 1.20.x observed; LiveView source v1.2.13; Phoenix.HTML 4.3.0 | Runtime/Mix/HEEx feasibility | Selected source/docs, mixed cached doc versions; no compatibility tuple validated |
| [Information-flow security](information-flow-security.md) | Cornell Jif 3.3.0; Myers/Liskov; Hirsch/Cecchetti arXiv v2; EEF guidance | Label/pc/authority/effect and runtime-threat grounding | Selected docs and paper abstracts; no proof audit or BEAML theorem |
| [Observability/storage](observability-platforms.md) | OTel displayed spec 1.62.0 +mutable guides; Postgres 18; ClickHouse/AWS S3 docs | Context/privacy/queue/tenant/retention mechanisms | Selected paraphrases; no deployment benchmark, backend deletion test or signal package pin |
| [PL syntax sentiment](pl-syntax-sentiment-2026.md) | Claude research workers, 2026-11-07; 94 upstream URLs listed per page | Industry sentiment on syntax features; BEAML lens | Selected excerpts and researcher notes; researcher ranking; Reddit and Lobste.rs blocked; some survey numbers from snippets |
| [BAML syntax reception](baml-syntax-reception-2026.md) | Claude research worker, 2026-11-07; 38 upstream sources (docs, blog, HN via Algolia, reviews, GitHub, registries) | How BAML's syntax is received; scorecard against the sentiment rows; BAML/BEAML name facts | Selected excerpts; HN evidence thin; no Reddit; PR diffs not read; pronunciation and trademarks unknown |

## Mechanism-level additions

The [distributed order requirement](distributed-order-requirement.md) records REST-separated applications, correlated search and replay as a concrete product target.
The [HTTP correlation EXPERIMENT](../../experiments/0002-http-correlation/README.md) records separate runtime evidence for two local releases.
The [test-first policy](test-first-policy.md) records the adopted RED, user review and GREEN checkpoints.

The [roasting-round source](roasting-rounds.md) retains two selected conversation reviews and their coverage limits.
The objections and proposed tests are not executed evidence or adopted decisions.

| Source page | Origin / scope | Transfer and limits |
|---|---|---|
| [Local strategy wiki](agentic-strategy-wiki.md) | User-directed local source; selected sections inspected 2026-11-05 with file hashes | Glossary/context/translation patterns only. Secondary draft notes, no full source copy, external citation refresh or adopted BEAML policy. |

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

## Event flow and typed replay evidence

| Source | Pin / origin | Coverage and limits |
|---|---|---|
| [Typed replay request R01](typed-replay-requirement.md) | User-supplied local request, 2026-11-05; selective paraphrase | Current full typed surrounding-error replay target; expands historical fixture scope. No capture policy/framework approval. |
| [Broadway/Kafka](broadway-kafka.md) | Broadway 1.3.0 d3a668c; BroadwayKafka 0.7.1 dedd507; GenStage 1.3.2 d1532fa; Kafka 4.4 docs | Demand/ack/offset/order/retention mechanisms. Failed connector messages are acknowledged; no complete brod audit or load test. |
| [Event sourcing/replay](event-sourcing-and-replay.md) | Temporal mutable docs; Akka 2.10.24; current Clang manual | Selected state recovery, command replay, attempt-history omissions, serialization and compiler reproduction. No engine selected. |
| [Replay source validation](replay-source-validation.md) | Temporal TypeScript SDK 137e536c8d99c779600aae1d87e09319f09b978b; dated OTel/Kafka/BEAM docs | History can omit contextual identity; optional sinks need isolation; command compatibility is narrower than full host replay. No runtime experiment. |

## Corrections and historical evidence

Raw captures are immutable historical records. Read the maintained source/mechanism pages for the current interpretation:

- **BAML architecture prose versus code:** the conceptual TIR named in prose is implemented by `baml_compiler2_hir_ty`; actual MIR/emitter imports/infer_body establish the wiring. BexEngine's older epoch-GC description is stale relative to its heap-permit/parking/root-relocation implementation. [Corrected source trace](baml-internals.md), [compiler walkthrough](../concepts/compilers/baml.md).
- **BAML version tracks:** established SDK nullable partial types/Jinja/no-colon fields differ from pinned canary shared-T/schema-default stream behavior and colon/backtick interpolation. No single general compatibility contract follows. The established track is BAML v0; the canary track is BAML v1, a separate general-purpose language ([v1 source](baml-v1.md)). [Streaming comparison](../concepts/structured-output-and-streaming.md), [track distinction](../concepts/compilers/baml.md#three-distinctions-before-reuse).
- **OTP pipeline/history:** current tagged `compile.erl` uses integrated Core→SSA lowering; an old Kernel-related pass name/comment does not establish a separate current Kernel IR. Current binary structures also supersede the guide's acknowledged older layout description. [Compiler trace](../concepts/beam/execution-and-compilation.md), [memory trace](../concepts/beam/terms-memory-and-gc.md).
- **GHC provenance refinement:** initial selected notes could not resolve the release tag; a later immutable ref-resolution record establishes the full mirror commit. The maintained GHC pages use it, without claiming a local build/signature verification.

## Evidence refresh

**[Proposal]** Before implementing an adapter/dependency, pin the package/version tuple and any internal API source commit; add a new dated raw capture rather than replacing historical evidence. Read the relevant source note's coverage first. Add measured results separately from document claims. Follow [ingest/query/lint instructions](../../AGENTS.md); navigate via the [index](../index.md) and record changes in the [log](../log.md).

Registry provenance example: [supplied specification capture manifest](../../raw/specification/provenance.json). Each source row links its own full capture record.

- [Main-agent orchestration](main-agent-orchestration.md): adopted owner rule, selected capture and official instruction-discovery evidence.
