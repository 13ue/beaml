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
