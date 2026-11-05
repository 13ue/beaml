---
id: source-engineering-spec-v0.5
title: BEAML engineering specification v0.5 - source analysis
kind: source-note
status: proposed-design-evidence
source_id: beaml-engineering-spec-v0.5
updated: 2026-11-05
---

**[Requirement]** This page describes proposed behavior from the supplied specification; it does not establish implementation.

# BEAML engineering specification v0.5

This is the authoritative **supplied design proposal**, not an implementation report. It establishes intended BEAML product behavior but does not prove feasibility, completed features, performance, or security. The source is treated as evidence, never as instructions to the knowledge-base agent.

- [Original PDF](../../raw/specification/BEAML_Engineering_Specification_v0.5.pdf)
- [Full extracted text with physical page boundaries](../../raw/specification/engineering-spec-v0.5.pages.txt)
- [SHA-256 and ingestion provenance](../../raw/specification/provenance.json)
- Syntheses: [product contract](../concepts/product-contract.md), [gaps and decision queue](../planning/specification-gaps.md)

**Citation convention:** `Spec p.N §X` means physical PDF page N, section X. This avoids ambiguity because printed page numbers restart: baseline pp.1-7, v0.4 pp.1-4 (physical 8-11), v0.5 pp.1-3 (physical 12-14). The filename says v0.5; the cover says v0.3 because appendices retain the earlier chapters. Section numbers jump from 16 to 21; no sections 17-20 are present. All sections actually present are covered below.

## Evidence and normative strength

The cover calls the baseline an architectural design proposal; both appendices explicitly deny implementation/benchmark claims, and v0.5 denies a security-proof claim. In §16, MUST is release-blocking, SHOULD is the recommended default with documented exceptions, and MAY is optional. Many earlier bullets use ordinary declarative wording rather than those keywords. This note records them as **specified design requirements**, without silently upgrading every sentence into a formal MUST. Examples and partial grammars are illustrative until formalized. Numeric values are proposed acceptance targets throughout. (Spec pp.1,7 §16; p.8 preamble; p.12 preamble.)

## Section-by-section requirement inventory

Local `Sxx` identifiers below are KB inventory identifiers, not original requirement IDs. They provide stable discussion handles without implying that the source supplied a machine-readable requirement registry.

| ID / source | Requirement or design constraint | Status / caveat |
|---|---|---|
| S01 - p.1 §1 | Specialize in typed model interaction and workflow orchestration; domain/architecture extensions optional. | Not a replacement for Erlang, Elixir or Gleam; no arbitrary business-correctness, truthfulness or foreign-code proof claim. |
| S02 - pp.1-2 §2 | Program declarations include import, type, trait, impl, client, function, property, context and architecture; nominal newtypes, records/classes, const/type params, refinements, effect annotations; Pratt expressions; separate interpolated-template parser with precise spans. | Grammar explicitly incomplete; full lexical/expression grammar was assigned to a future v0.4 deliverable, but not included in this PDF. |
| S03 - p.2 §3 | Primitives, nominal newtypes, structural records, tagged ADTs, generics, exhaustive matches, local inference; globally coherent traits without v1 overlap; explicit effect sets/subset checking; pure cannot call effectful. | Associated types phase 2; higher-kinded types/GADTs/type families later. |
| S04 - p.2 §3 | Constant/interval refinement proofs first; unsupported/undecidable predicates require explicit checked conversion; natural-number const expressions restricted. | Predicate fragment and solver rules unresolved. |
| S05 - p.2 §3 | Generic model output requires a Schema witness via monomorphization or typed dictionary; typestate Pending/Streaming/Validated/Complete. | Choice of witness representation unresolved; affine stream ownership later. |
| S06 - p.2 §3 | Untrusted JSON -> parsed T -> validated T -> refinement-checked value; validation returns errors. Preserve missing versus explicit null when schema distinguishes them. | Schema conformance is not factual truth; provider/network failures remain explicit in generated API. |
| S07 - pp.2-3 §4 | Rust standalone compiler invoked by Mix; lexer/lossless CST/AST/resolved HIR/checking/typed MIR/generated source/BEAM compiler; retain semantic IDs and source maps. MIR carries CFG, effects, obligations and instrumentation. | Emit Elixir/Erlang-compatible source first; direct BEAM bytecode out of scope. |
| S08 - p.2 §4 | Deterministic incremental queries, tracked dependencies, cycle diagnostics; cache identity includes compiler version, feature flags, schema capabilities and imported interface fingerprints. | Warm prompt-literal edit should leave unrelated type queries valid; precise invalidation protocol absent. |
| S09 - p.3 §4 | Safe typed core avoids language-level type mismatch stuckness subject to explicit foreign/runtime effects; lowerings preserve supported observable semantics; recovery must not accept ill-typed programs. | Compile-fail, MIR goldens, differential, fuzz and property tests are release gates; no proof supplied. |
| S10 - p.3 §5 | Same semantic DB for LSP, unsaved overlays, regional reparsing where possible, malformed/incomplete code tolerance; type-aware completion, navigation, refactors, diagnostics, hover, tokens, hints, actions, formatting. | Protocol version chosen/verified for release; editor plugins cannot duplicate semantics; version edits and reject stale client versions. |
| S11 - pp.3-4 §6 | Type-derived Arbitrary; constructive/solver refinement generation; report generator exhaustion rather than pass; accepted shrink steps preserve type/refinement. | Stateful runner executes reference model + SUT adapter and shrinks traces preserving preconditions; record seed/compiler/generator/minimal case; concurrency scheduler testing later. |
| S12 - p.4 §7 | Optional DDD constructs: contexts, aggregates, commands, events, invariants/pre/postconditions; version event schemas and check breaking compatibility. | Pure transitions analyzable; DB atomicity, external effects and distributed consistency need runtime/integration guarantees. |
| S13 - p.4 §8 | Structural architecture checks from symbol/dependency graph; semantic checks from HIR/MIR/effects; sensitive telemetry flow uses conservative taint analysis. | Opaque foreign calls may be inconclusive; inconclusive must be surfaced. |
| S14 - pp.4-5 §9 | Contract proof status mandatory; manifests include obligation ID, source span, checker version, status, evidence reference and runtime hook. | PROVEN/ENFORCED/TESTED/UNKNOWN/VIOLATED semantics below; later appendices rename statuses. |
| S15 - p.5 §10 | Compiler-generated stable operation IDs, trace/span context, type/schema versions, effects, validation paths, source maps; distinguish workflow edges from process links; explicit message context propagation. | Metadata-only default, sensitive values absent/redacted; replay only permitted fixtures/provider responses, not arbitrary BEAM scheduler replay; exporters/logs are effects. |
| S16 - pp.5-6 §11 | Reproducible compiler/LSP/runtime/fuzz budgets with pinned reference environment, >=30 runs, p50/p95/max/confidence interval; exclude network/model latency. | Targets, not measured results; >=95% cache-hit target only controlled single-function edit; report generator categories separately. |
| S17 - p.6 §12 | Per-feature parser/recovery/formatter, typing/diagnostic/inference, MIR differential/reproducibility, LSP/stale-edit, checker/counterexample/foreign-boundary, provider/cancel/timeout/retry/privacy coverage. | Release requires no unresolved P0/P1 defects, mandatory tests pass, no over-budget regression without signed exception. |
| S18 - p.6 §13 | Rust compiler crates, BEAM runtime/testing/telemetry, VSCode editor, benchmarks/fixtures/specifications. | Intended module boundaries; small initial crates may combine; semantics must not be duplicated. |
| S19 - p.7 §14 | M0-M8 phased delivery with explicit exits. | Table below; roadmap is proposed, not completed. |
| S20 - p.7 §§15-16 | Record listed unresolved semantics; language feature stability requires syntax, typing, dynamics, diagnostics, interop and tests. | Formal typing/evaluation, trait rules, MIR invariants, query invalidation and complete EBNF are next deliverables. |
| S21 - p.8 §21 | BEAML owns domain/application types, commands, validation, effects and optional UI contracts; Elixir owns callbacks, markup/components, routes, Ecto adapters and OTP; generated versioned ABI decodes/validates. | Constructing an ordinary Elixir struct grants no trusted BEAML status. |
| S22 - p.8 §22 | Optional UI contracts specify assigns, literal event discriminants, payloads, forms, component props/slots; decode untrusted string-keyed maps; check render entry and recognized assign transformations. | Conditional/dynamic/metaprogrammed cases require fallback diagnostics; example grammar illustrative. |
| S23 - p.8 §23 | Stable typed descriptors, decode_event/2, form/0, change/2, assign/2, field references; explicit {:ok, value}/{:error, error} ABI. | Example also uses put_error but its ABI contract is not specified. |
| S24 - p.9 §24 | Official Phoenix/HEEx parser plus available Elixir semantics; HIR IDs/spans; no regex template analysis. Check assigns, fields/refinements, props/slots, literal events/payloads, statically knowable handlers. | Supported static subset only; dynamic unknown flagged; phx-value-* strings require decoding and never imply InvoiceId. |
| S25 - p.9 §25 | UI-001..006 diagnostics; .beaml/.heex/supported ~H LSP completion, hover, definition, refs, rename, tokens/actions/diagnostics. | Separate HEEx/Elixir frontends, one BEAML query DB; source-preserving rename refuses unsafe dynamic edits. |
| S26 - p.9 §26 | RawFormParams -> ParsedInput -> Validated; partial editing returns field diagnostics, not aggregate validity; server validation authoritative. | Optional/missing/empty-string/null semantics must be specified separately; client constraints only hints. |
| S27 - pp.9-10 §27 | Prevent web imports in pure domain; tracked sensitive flows cannot reach telemetry; dynamic Elixir/macros/NIFs/reflection/untracked libs explicit boundaries. | Classify every claim PROVED/RUNTIME_ENFORCED/TESTED/UNKNOWN. |
| S28 - p.10 §28 | Typed refined generators/shrinkers; full BEAML->generated API->event decode->command->HEEx tests including malformed/missing/nested/malicious/optional/union/slot/error-render cases. | Invalid rejected payload property requires zero domain effects. |
| S29 - p.10 §29 | Reproducible HEEx performance + correctness + boundary/conformance budgets. | Separate false positive/negative counts; unsupported -> UNKNOWN; benchmark cannot establish soundness. |
| S30 - p.11 §30 | UI delivery A-F from grammar through adapters/parser/LSP/analysis/property testing. | Gates below. |
| S31 - p.11 §§31-32 | No HEEx replacement, arbitrary Elixir compilation/proof, or client-validation security reliance; feature done only with grammar, typing, maps, ABI, diagnostics, negative tests, dynamic handling, benchmark fixture. | Every generated entry point validates browser input before domain execution; parser/schema/component/dynamic/metadata/enforcement choices open. |
| S32 - p.12 §33 | Default prevent unauthorized sensitive flow within compiler-controlled boundary; declare TCB and scoped testable assurances. | Foreign code, NIFs, hosts, side channels, recipients and infrastructure limit guarantees; no blanket secrecy claim. |
| S33 - p.12 §34 | Value labels propagate through interpolation/concat/format/collections/records/variants/maps/errors/derived values. | Bare String cannot erase sensitivity: reject or infer sensitive; no implicit downgrade. |
| S34 - p.12 §35 | Lattice spans confidentiality public/internal/confidential/secret, data categories, purposes/recipients; join restrictions; pc label tracks branch implicit flow; sink check includes context. | v1 rejects analyzable secret-dependent public output branches; timing/size/cardinality leakage not comprehensively eliminated. |
| S35 - p.12 §36 | Explicit policies for telemetry, browser, LLM and HTTP sinks; declassification privileged capability with policy, justification, principal/purpose, reviewed allowlist, metadata audit, generated callsite ID. | Prefer vetted masking/tokenization/aggregation; masks require leakage budget/output guarantee, not automatic anonymity. |
| S36 - p.13 §37 | Public API opaque handles/sealed values where possible; unknown foreign functions potentially leaking absent reviewed effect/taint manifest; strict mode blocks/unknowns dynamic boundaries. | Authorized user-scoped PII render is explicit authorization, not global downgrade; no PII in phx-value attributes, URLs, inspect, flash. |
| S37 - p.13 §38 | Secrets from manager/environment, never source/artifacts; minimize copies, prevent routine inspect/serialization, zeroize where feasible; encryption/least privilege/rotation/dump controls. | Runtime representation SHOULD minimize exposure; BEAM GC precludes universal erasure guarantee; redaction defense in depth. |
| S38 - p.13 §39 | Compiler->Phoenix/OTP adapter->local policy/redaction->OTel Collector->storage; local/self-hosted/optional managed; no required remote exporter. | Reference ClickHouse traces + Postgres app metadata + optional encrypted S3 replay; small deployment may start traces in Postgres. |
| S39 - p.13 §40 | ObservationEvent fields listed below; stable IDs/maps/context and public sanitized attributes; payload OFF. | Sensitive values cannot stringify/inspect/hash into stable identifiers/serialize to traces; even IDs, paths, errors, prompt templates may be sensitive. |
| S40 - pp.13-14 §41 | Proposed trace/error/metric/replay retention defaults; bounded buffers/batching/loss counts; routine telemetry outage cannot block business operations; discard low priority rather than unbounded sensitive spools. | Durable security audit uses separate explicit failure policy; provider replay differs from scheduler replay. |
| S41 - p.14 §42 | Trace/type/contract/process/model/exception/privacy/audit/admin product surfaces. | Tenant isolation, RBAC, audited observability access. |
| S42 - p.14 §43 | HIR label inference, control-flow MIR propagation, pre-codegen sink verifier; preserve security labels/effects across all IR/optimization passes; explicit IR release, security manifest/map, boundary runtime guards. | Exact formal model and pass proofs not supplied. |
| S43 - p.14 §44 | Mandatory compile-fail/IR/canary/fuzz/interop/strict-logging gates and broad sink/exception/interop corpus. | Canary sink search is evidence, not proof; property-test joins + preserving shrink. |
| S44 - p.14 §45 | P0/P1/P2 rollout below; production fails closed on unclassified sensitive egress, payloads off, no implicit declassification. | Priorities are rollout stages here, distinct from §12 defect severity. |
| S45 - p.14 §46 | Each security rule needs syntax, formal flow rule, boundary, positive/negative tests, code, interop, limitation, runbook; status scoped to formal model. | PROVED/RUNTIME_ENFORCED/TESTED/UNKNOWN; no no-leak blanket promise. |

## Exact acceptance targets and reproducibility contracts

### Baseline compiler/runtime (§11, physical pp.5-6)

Reference runner: Linux x86-64, 8 dedicated vCPUs, 32 GiB RAM, local NVMe, warm filesystem cache, pinned compiler/runtime. At least 30 iterations; p50, p95, maximum, confidence interval. Network/model latency excluded.

| Metric | Proposed target | Fixture |
|---|---|---|
| Full compile | p95 <=2.0s | 10k LOC, 100 modules, warm disk, cold semantic cache |
| Incremental compile | p95 <=200ms | One function edit, 10k LOC |
| Completion / hover / definition | p95 <=100 / 50 / 75ms | 10k LOC, warm query cache |
| Rename | p95 <=500ms | 1,000 references, 10k LOC |
| Architecture check | p95 <=1s | 100k LOC, warm semantic cache |
| Property runner | >=10k cases/s | Pure scalar, one thread; nested/refined/stateful separately reported |
| Compiler RSS | <=1.5 GiB | 100k LOC clean build |
| Telemetry overhead | <=5% CPU | Synthetic metadata-mode runtime workload |
| Fuzz | 0 crashes over >=10M malformed inputs | Across parsers; evidence, not safety proof |
| Cache hit ratio | >=95% optimization target | Controlled single-function edit only |

### UI (§29, physical p.10)

Pinned machine: 8 modern performance cores, 32 GiB, local SSD. Warm/cold separately; 30 runs; p50/p95/p99; fixtures 10k/100k BEAML LOC and 100/1,000 templates. Exclude editor/network latency; record revision, OTP/Phoenix and OS. This differs from the baseline benchmark environment/summary statistics and needs a unified protocol before comparing results.

| Metric | Proposed gate |
|---|---|
| HEEx completion / hover | p95 <=100 / 50ms; 1k templates warm index |
| Incremental diagnostics | p95 <=200ms; single-template edit |
| Project rename | p95 <=500ms; 1,000 static references |
| Architecture | p95 <=1s; 100k LOC warm |
| Semantic correctness | >=99% curated versioned labeled fixtures; report false positives/negatives separately |
| False-safe | 0 known; unsupported -> UNKNOWN |
| Fuzz | 0 crashes /10M parser + HEEx adapter inputs |
| Validation bypass | 0 in conformance suite; every generated public entry |

### Security (§44, physical p.14)

| Gate | Proposed target / evidence |
|---|---|
| Unauthorized sink flows | 0 accepted golden compile-fail cases |
| Label preservation | 100% tested IR passes; property + metamorphic tests |
| Telemetry PII leaks | 0 in canary corpus; end-to-end sink inspection |
| Fuzz | 0 /10M parser + label engine + adapter cases |
| Interop | 100% callsites classified; manifest CI |
| Strict secret logging | 0 accepted; Elixir/HEEx boundary tests |

Coverage includes direct/implicit leaks, nested structs, errors/exceptions, inspect/format/interpolation, HTML/phx-value, PubSub, Ecto logs, HTTP, LLM, Oban arguments, crash dumps and dynamic interop. Zero observed failures is not a universal proof.

## Delivery and exit criteria

| Baseline phase (§14 p.7) | Deliverable | Exit |
|---|---|---|
| M0 | Formal core/spec | Typing/evaluation rules + 100 normative examples |
| M1 | Parser/CST/diagnostics | 1M parser fuzz cases, zero crashes |
| M2 | Types/generics/ADTs | 500 compile-pass/fail fixtures |
| M3 | MIR/BEAM backend | End-to-end validated extraction demo |
| M4 | Incremental/LSP | Hover/definition/rename +target latency tests |
| M5 | Properties/shrinking | Seed replay +invariant-preserving shrink |
| M6 | DDD/architecture | Static checks +model-based tests |
| M7 | Observability/replay | Trace graph +redaction tests +fixture replay |
| M8 | Hardening/release | Performance budgets +10M fuzz cases |

| UI phase (§30 p.11) | Deliverable | Gate |
|---|---|---|
| A | Contract grammar/typed descriptors | Golden +grammar tests |
| B | Phoenix form/event adapters | End-to-end validation |
| C | HEEx parser/cross-references | Unknown boundaries reported |
| D | LSP diagnostics/completion/rename | Performance +fixture gates |
| E | Props/slots/assigns/effects | Regression +architecture |
| F | UI property testing | Reproducible seeds +shrinking |

Security rollout (§45 p.14): **P0** labels/propagation, strict sinks, redacted telemetry, unknown interop diagnostics, minimal OTLP+Postgres Observatory. **P1** ClickHouse, process graphs, policy-aware HEEx, declassification approvals, security manifests/CI. **P2** advanced implicit flow, vetted masking/tokenization, encrypted replay, distributed lineage, stronger formal verification. No dependency ordering between M/A/P tracks is supplied.

## Proof-status vocabulary (do not collapse these)

Baseline §9 (pp.4-5): **PROVEN** = discharged by supported sound static rules, accepted; **ENFORCED** = runtime validator, accepted with runtime tests; **TESTED** = observed executions, no proof; **UNKNOWN** = inconclusive, explicit waiver or reject; **VIOLATED** = counterexample/static violation, reject. Later §§27/46 (pp.10/14) use **PROVED / RUNTIME_ENFORCED / TESTED / UNKNOWN**, without specifying a migration or explicit VIOLATED status. Preserve original terms until a schema is chosen. A policy waiver is not a proof.

## Operational data contracts

ObservationEvent (§40 p.13): event_id UUID, trace_id TraceId, span_id SpanId, parent_span_id Option<SpanId>, process_id OpaquePid, semantic_id DefinitionId, source_map_id SourceMapId, event_kind EventKind, timestamp Instant, duration_ns Option<Int>, outcome Outcome, attributes Map<String, PublicTelemetryValue>, schema_version Int. Exact enum definitions, encoding/transport and compatibility rules remain absent.

Retention defaults are proposals (§41 pp.13-14): technical traces 14d; error traces 30d policy-filtered; aggregated metrics 90d with bounded cardinality; prompt/response bodies OFF (consent/purpose required); replay OFF or opt-in 7d encrypted/scoped/deletable. Routine telemetry is lossy/bounded under outage; durable security-audit behavior must be separately specified.

## Follow-up reading questions

This source establishes desired constraints. External research should test the mechanisms without rewriting these proposals into settled decisions: official Phoenix parser/compiler APIs and version support; BEAM interop/process cancellation/atom and secret handling; BAML schema/streaming concepts and semantic differences; incremental Rust query and source-map strategies; refinement/model-based testing; formal information-flow + pc/declassification models; OTel privacy/backpressure and Postgres/ClickHouse storage. See [gap inventory](../planning/specification-gaps.md) for the decision queue.
