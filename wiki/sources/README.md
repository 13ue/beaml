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

## Evidence refresh

**[Proposal]** Before implementing an adapter/dependency, pin the package/version tuple and any internal API source commit; add a new dated raw capture rather than replacing historical evidence. Read the relevant source note's coverage first. Add measured results separately from document claims. Follow [ingest/query/lint instructions](../../AGENTS.md); navigate via the [index](../index.md) and record changes in the [log](../log.md).

Registry provenance example: [supplied specification capture manifest](../../raw/specification/provenance.json). Each source row links its own full capture record.
