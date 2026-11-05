---
id: concept-observability-and-replay
title: Observatory, telemetry and replay boundaries
kind: synthesis
status: research-backed-proposal
updated: 2026-11-05
---

# Observatory, telemetry and replay

**[Requirement]** Observatory is compiler-aware operational visibility: stable semantic/source identities, type/schema and contract context, workflow causality, OTP topology and model metrics. The proposed pipeline is compiler instrumentation -> Phoenix/OTP adapter -> local policy/redaction -> Collector -> storage. Payloads default OFF; routine collector failure cannot block business work. [Spec p.5 §10; pp.13-14 §§39-45](../sources/engineering-spec-v0.5.md). [Platform source notes](../sources/observability-platforms.md) record current primary evidence and limits.

## Safe instrumentation starts before export

**[Requirement]** Only sanitized `PublicTelemetryValue` attributes enter ObservationEvent; prompts/responses, sensitive IDs/errors/paths/templates and sensitive-derived stable hashes cannot be smuggled into traces. Source maps and stable operation IDs do not grant permission to capture user values. Logs/exporters are external effects. (Spec§§10,40.)

**[Verified]** [OTel guidance](https://opentelemetry.io/docs/security/handling-sensitive-data/) leaves sensitivity classification to the implementer and provides Collector cleanup tools; it warns about predictable-domain hashes. **[Inference]** Post-capture regex cleanup cannot substitute for BEAML's compiler/sink boundary, because the rejected data would already have reached adapter memory or other sinks. **[Proposal]** Generate typed allowlisted attributes at the source, apply a second local policy check before OTLP, and test all body/attribute/event/resource/error channels with canaries. Avoid importing upstream hashing examples as if they satisfied the stricter BEAML requirement.

## Context is not authorization

**[Verified]** OTel's [Erlang propagation](https://opentelemetry.io/docs/languages/erlang/propagation/) describes HTTP instrumentation and process-dictionary context; its [baggage warning](https://opentelemetry.io/docs/concepts/signals/baggage/) includes unintended propagation and absent integrity checks. **[Proposal]** Pass a small explicit trace carrier across BEAML-controlled tasks/messages and restore it with bounded lifetime. Keep authenticated principal/purpose state separately verified; incoming baggage cannot confer permission. Sensitive/user identifiers should not enter baggage by default.

**[Requirement]** Logical workflow edges differ from process links/supervision (Spec§10). **[Verified]** [OTel tracing API](https://opentelemetry.io/docs/specs/otel/trace/api/) offers a parent tree plus additional span links. **[Proposal]** Record command/provider/event causality with span parent/links as appropriate and maintain process/supervision relations separately. Test fanout, batch work, cancellation and restart; close spans on every completion/error path. The API's availability does not establish BEAML message propagation automatically.

**[Verified]** [Erlang OTel status](https://opentelemetry.io/docs/languages/erlang/) distinguishes stable traces from development metrics/logs as checked 2026-11-05. **[Proposal]** Pin API/SDK/exporter and instrumentation versions per signal before claiming the whole Observatory pipeline is production-ready.

## Bounded loss and durable audit need distinct policies

**[Requirement]** Bounded buffers, batching and loss counters; drop low-priority ordinary observations on outage rather than unbounded sensitive spools. Security audit requiring durable delivery has separate explicit failure behavior. (Spec§41.) **[Verified]** [Collector resiliency](https://opentelemetry.io/docs/collector/resiliency/) offers finite queues/retries and optional disk WAL; neither guarantees zero loss.

**[Proposal]** For the first local probe, use metadata-only bounded memory, enforce a byte/item cap, and expose safe dropped-count/queue-size metrics. Simulate collector outage and verify commands continue, memory stays bounded, loss is visible and no secret-bearing local spool appears. An opt-in durable audit path needs its own encryption/access/retention/retry/acknowledgment contract and explicit business failure policy. Do not obtain “reliability” by silently persisting more sensitive data.

## Start with specified storage phases, measure the transition

**[Requirement]** P0 minimal OTLP+Postgres; P1 ClickHouse. Reference larger architecture separates traces/events, application metadata and optional encrypted S3 replay; small deployment Postgres traces is permitted. Proposed defaults: traces 14d, errors 30d, metrics 90d, replay OFF/opt-in 7d. (Spec§§39,41,45.)

**[Proposal]** Begin one local tenant-aware Postgres store and a minimal trace/source/contract view. Add ClickHouse only after measuring ingest volume, retention cost and query p95 against declared fixtures; do not invent a migration threshold without measurements. Avoid general dashboards or managed service until boundary and storage tests work.

**[Verified]** [PostgreSQL 18 RLS](https://www.postgresql.org/docs/18/ddl-rowsecurity.html) has owner/superuser/BYPASSRLS exemptions. **[Proposal]** Test real application roles and malicious tenant filters, background jobs and admin/report routes; audit Observatory reads. RBAC and tenant isolation remain required beyond any single database feature.

## Replay is a separately consented artifact

**[Requirement]** Replay records explicitly allowed fixtures/provider responses, encrypted with scoped access and delete support; it is not deterministic arbitrary scheduler replay. (Spec§§10,41.) **[Proposal]** Record compiler/schema/provider configuration identifiers, the allowed request/response fixture boundary, consent/purpose/policy version and expected validator result. Keep secrets out; nondeterministic provider behavior/scheduler ordering cannot be reconstructed from spans alone.

**[Verified]** [ClickHouse TTL](https://clickhouse.com/docs/concepts/features/operations/delete/ttl) deletes during merges; [Amazon S3 expiry](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html) is asynchronous and version-aware, potentially leaving noncurrent versions. **[Inference]** Retention eligibility, query invisibility and physical erasure are different lifecycle outcomes. **[Proposal]** Replay acceptance tests must enumerate actual object versions, encrypted backups/replicas and source/index references after deletion; set and document backend-specific timing. “S3-compatible” alone does not establish Amazon's exact behavior.

**[Unknown]** Storage schemas, retention guarantees, deletion deadlines, key management, consent revocation, audit durability, export authentication, overhead and tenant isolation are not implemented or benchmarked. The next useful validation is a small canary/outage/cross-process/tenant probe, not a broad product-surface build.

## Typed event mapping and sampling

**[Proposal]** Map ObservationEvent by semantic purpose, not by stringifying the whole record. This is an unexecuted candidate, not a finalized ABI:

| BEAML fact | Candidate OTel representation | Invariant / rejected shortcut |
|---|---|---|
| An operation with duration/outcome | Span start/end/status and approved stable operation name | Never put raw request/prompt/customer value in span name |
| A point violation/readiness transition | Approved span event or correlated structured log | Stable event kind and field path policy; field value absent |
| trace/span/parent | Native context fields | Keep process/supervision edges separate; fan-in may use links |
| semantic/source/schema IDs | Allowlisted attributes plus artifact identity | Source-map access can reveal code/paths; authorize navigation |
| Public attributes | Typed bounded attributes | No implicit Inspect/ToString; validate key/value/size/category |
| count/latency/token/cost estimates | Counter/histogram with bounded dimensions | Preserve unit, attempt/final-success semantics and estimate status |

**[Verified]** The [OTel logs model1.62.0](https://opentelemetry.io/docs/specs/otel/logs/data-model/) distinguishes event time, observation time, context, body, attributes, resource and scope. **[Proposal]** Preserve event time versus collector arrival time; use monotonic clocks for local durations and report clock assumptions for distributed ordering. Resource/scope/schema metadata needs the same privacy review as ordinary attributes. A sanitized span with a sensitive resource key is still a leak.

**[Verified]** [Tracing SDK sampling1.62.0](https://opentelemetry.io/docs/specs/otel/trace/sdk/#sampling) separates dropped, recorded-only and recorded+sampled decisions. **[Inference]** “Not exported” does not imply “not collected”: record-only data can exist in process memory/processor paths. **[Proposal]** Apply policy before recording, not after sampling; use head sampling for predictable budgets and consider tail sampling only with an explicit bounded buffering/trust design. Audit events that require durable capture cannot depend on ordinary probabilistic trace sampling. Sampled trace totals are not automatically exact token/billing totals.

## Cardinality and metric meaning

**[Proposal]** If dimensions are 20 operations ×4 outcomes ×3 providers, the nominal combination bound is 240 series before extra dimensions. Adding per-customer identifiers for 100,000 customers can multiply that to 24 million; it also introduces sensitive tracking. Prefer fixed operation/provider-class/outcome dimensions and reviewed aggregate views. Limit attribute count/value bytes and distinct series at ingestion, with visible overflow/drop accounting.

**[Verified]** [Metrics SDK cardinality rules1.62.0](https://opentelemetry.io/docs/specs/otel/metrics/sdk/#cardinality-limits) define unique attribute combinations and overflow aggregation, with filtering before limits. **[Proposal]** Verify the chosen Erlang implementation supports the needed behavior rather than assume the specification's general feature is present. Define retries as attempt metrics plus one terminal workflow result; otherwise latency/cost counters double-count or conceal failed attempts. A cost estimate needs model/price revision, unit and uncertainty; it is not an invoice.

## Queue arithmetic and failure transitions

**[Proposal]** For a bounded queue of 10,000 events, producer rate 2,000/s and zero downstream throughput, nominal fill time is 5s. At average 512 bytes/event the payload lower bound is about 5.12MB; BEAM terms, queue structures, serialization and batches add overhead. When inputλ exceeds outputμ, fill time from empty is approximately cap/(λ−μ). Bound bytes as well as count so one oversized error cannot consume the budget. These are planning calculations, not observed measurements.

**[Verified]** [Tracing SDK processor/batch rules](https://opentelemetry.io/docs/specs/otel/trace/sdk/#built-in-span-processors) have synchronous callbacks, queue bounds and flush timeouts; [Collector configuration](https://opentelemetry.io/docs/collector/configuration/#processors) preserves configured processor order. **[Proposal]** Keep synchronous instrumentation bounded and nonblocking; local policy before batching/export and before any permitted persistent queue. Check every fan-out pipeline, debug exporter and self-diagnostic sink; one redacted exporter does not cover another raw branch. Version the resolved final configuration/component set, auth/TLS and secret references.

**[Verified]** [OTLP 1.11.1 partial success](https://opentelemetry.io/docs/specs/otlp/#partial-success) can return HTTP200 with rejected counts; populated partial_success must not be retried wholesale. Retryable/nonretryable failures differ. **[Proposal]** Test full success, partial acceptance, bad data, recoverable outage, auth failure, request/response limits, timeout and ambiguous disconnect after server acceptance. Event IDs can support deduplication where a storage path needs it, but OTLP acceptance alone is not an end-to-end exactly-once/durable acknowledgment. Never turn remote error text into unfiltered public telemetry.

## Durable security audit is a separate transaction problem

**[Requirement]** Routine telemetry remains lossy/nonblocking; durable audit has an explicit failure policy (Spec§41). **[Verified]** OTel [error-handling principles](https://opentelemetry.io/docs/specs/otel/error-handling/) protect application behavior from runtime telemetry failures. Postgres 18 [WAL settings](https://www.postgresql.org/docs/18/runtime-config-wal.html#GUC-SYNCHRONOUS-COMMIT) distinguish acknowledged commit from durable flush; asynchronous commit can lose recent acknowledged work after crash. [Reliability guidance](https://www.postgresql.org/docs/18/wal-reliability.html) adds hardware/cache assumptions.

**[Proposal]** For a policy requiring “no sensitive release without durable audit,” define the commit boundary: authorize +persist a metadata audit/outbox record durably, then perform/record the allowed release with idempotent operation identity. Decide what happens if the process dies between audit and egress, or egress succeeds before acknowledgment: retries can duplicate a release; an audit of intent is different from proof of delivery. Local/outbox transactions cannot atomically commit an arbitrary external recipient, so document at-least-once/uncertainty and reconciliation. Routine span failure must not adopt this blocking behavior by accident. No audit/outbox system is implemented here.

## Tenant isolation, deletion and replay runbook shape

**[Proposal]** Derive tenant identity from authenticated server context, never incoming event attributes. Validate ingest credentials against tenant/project routing; run queries under intended restricted roles; apply access checks to source maps, saved searches, exports, exception drilldowns and replay. Include worker/admin/backup access and observation of cross-tenant aggregate counts. [Postgres RLS](../sources/observability-platforms.md) is one defense; [ClickHouse row-policy documentation](https://clickhouse.com/docs/reference/statements/create/row-policy) must be checked against the chosen roles/table privileges. A user able to modify/copy underlying data is outside a mere SELECT-filter guarantee.

**[Proposal]** A replay artifact should have a registry row linking tenant, consent/purpose/policy version, compiler/schema/provider fixture version, encryption/key reference, object+version identifiers, expiry and deletion status. On revoke/expiry: disable reads/replay first; enumerate and remove permitted object versions/index references; account for replicas/backups/retention locks and failed cleanup; retain a non-sensitive deletion audit with bounded lifetime. **[Verified]** [Amazon's versioned deletion semantics](https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html) show why GET404 or a delete marker does not prove object erasure. Compatible backends require their own tests.

**[Proposal]** The first operational suite uses unique canaries in ordinary fields, errors, metadata, baggage and fake secrets; exercises queue saturation/collector crash/restart/disk full/partial success/tenant-role misuse/consent revocation; then inspects every configured sink and storage version. Measure business latency/CPU/memory with telemetry disabled/enabled/outage and report lost data explicitly. **[Unknown]** Backend configuration, durable audit contract, sampling semantics, cardinality policy and deletion deadlines remain unselected/unexecuted; sufficient reference mechanisms do not constitute their validation.
