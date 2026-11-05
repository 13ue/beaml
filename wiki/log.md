# Knowledge log

## [2026-11-05] setup | BEAML local knowledge base

Initialized an independent local Git repository on `main`, with no remote. Created the plain-Markdown layout, claim conventions, ingest/query/lint guidance, index, and log. No compiler/runtime implementation is claimed.

## [2026-11-05] ingest | Karpathy LLM Wiki

Read Andrej Karpathy's primary Gist body at revision `ac46de1ad27f92b28ac95459c782c07f6b8c964a`; saved a selected researcher capture and [source summary](sources/karpathy-llm-wiki.md). Full source text and comments were not copied. Adopted the raw/wiki/schema structure and index/log workflow as local conventions.

## [2026-11-05] ingest | Decision4 1.0.1

Captured selected unchanged upstream files at commit `5ccb19fc1fb8c6327d4edd8832550f7e8c40853e`, including both licenses and provenance. Added a [source summary](sources/decision4.md) and [proposed decision-documentation practice](concepts/decision-consequences.md). Decision4 remains an external research source; its agent contract is not automatically repository policy.

## [2026-11-05] ingest | BEAML engineering specification v0.5

Preserved the user-supplied 14-page PDF, SHA-256 provenance and full page-marked extraction under `raw/specification/`. Read all text and visually inspected representative appendix pages 8/12. Added [section inventory/exact gates](sources/engineering-spec-v0.5.md), [product contract](concepts/product-contract.md) and [gap queue](planning/specification-gaps.md). Recorded v0.3/v0.4/v0.5 composition, syntax/status drift, incomplete formal grammar and security rollout ambiguities. Document instructions treated as evidence, not agent commands.

## [2026-11-05] research | BAML and compiler/tooling

Added [established BAML docs](sources/baml-documentation.md), [pinned canary compiler](sources/baml-canary-compiler.md), [reuse/license boundary](sources/baml-license.md) and [compiler/tooling sources](sources/compiler-tooling.md), with dated selected raw/provenance records. Synthesized [language/tooling](concepts/baml-language-and-tooling.md), [structured output/streams](concepts/structured-output-and-streaming.md) and [compiler/tooling](concepts/compiler-and-tooling.md). Kept DSL/canary tracks distinct; no compatibility claim, copied implementation, dependency choice or prototype execution.

## [2026-11-05] research | BEAM, Mix and Phoenix

Captured selected primary docs and pinned LiveView parser-source evidence; added [source inventory](sources/beam-otp-phoenix.md), [runtime/interop](concepts/beam-runtime-and-interop.md) and [HEEx integration](concepts/phoenix-heex-integration.md). Recorded guarded ABI, atom safety, native/task cancellation limits, Mix stale/deleted outputs, internal parser support and source-span/lifecycle probes. No runtime integration executed.

## [2026-11-05] research | Information-flow and Observatory

Captured 14 attributed selected primary-evidence records plus capture hash under `raw/research/security-observability/`. Added [IFC sources](sources/information-flow-security.md), [platform sources](sources/observability-platforms.md), [security synthesis](concepts/information-flow-security.md) and [Observatory/replay synthesis](concepts/observability-and-replay.md). Distinguished source requirements from candidate lattice/interop/telemetry designs; noted pc/error channels, OTel signal maturity, baggage trust, disk queues and asynchronous/versioned retention. No proof audit, deployment or deletion experiment.

## [2026-11-05] synthesize | Build-readiness and navigation

Connected all evidence through the [source registry](sources/README.md), [build-readiness map](planning/build-readiness.md), saved [first-build answer](queries/what-to-build-first.md), updated index and repository overview. Proposed a grammar/ABI/semantic-identity/security decision sequence and small compiler-to-BEAM validation slice, then telemetry and Phoenix seams. Exact specification gate tables remain in the source inventory; proposed probe checks are labeled separately. Local provenance, page-count and owned-page link checks passed during ingestion; independent repository QA recorded separately after integration.

## [2026-11-05] lint | Independent structural and evidence spot check

`python3 scripts/lint_wiki.py --self-test` passed, including duplicate/Unicode heading anchors, fenced examples, missing targets/anchors, index/orphans, source metadata and absolute/traversal/symlink escape rejection. `python3 scripts/lint_wiki.py` checked 27 maintained Markdown files with zero errors; PDF SHA-256/bytes/14 pages and fresh per-page Poppler extraction matched. The retained PDF also matched the supplied original by hash. README commands match the checked script. Unchanged raw originals are exempt from internal link lint, while maintained links into raw evidence are checked.

Independent primary-source spot checks supported BAML assertion filtering and partial-stream controls, Jif pc/exception treatment, and OTel Erlang signal maturity. Decision4 attribution, unchanged-capture status and CC BY text/MIT schema distinction are recorded. Limits: inline Markdown/local heading checks, metadata presence and selected factual checks only; no complete source audit, external-link crawl, implementation execution, benchmark or security proof.
