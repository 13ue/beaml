---
id: source-observability-platforms
title: Observability and storage primary evidence
kind: source-note
status: verified-upstream-not-beaml
updated: 2026-11-05
---

# Observability and storage primary evidence

**[Verified]** describes upstream documentation checked 2026-11-05. These are candidate mechanisms, not BEAML deployment facts. [Local selected-evidence record](../../raw/research/security-observability/2026-11-05-selected-evidence.md) contains coverage and attribution. Mutable documentation needs version/commit pinning when implementation starts. See [Observatory synthesis](../concepts/observability-and-replay.md).

| Primary source | Inspected fact | BEAML consequence / limitation |
|---|---|---|
| [OTel sensitive-data guidance](https://opentelemetry.io/docs/security/handling-sensitive-data/) | Implementer determines sensitivity; processors support removal/filtering/allowlisting/transforms; predictable hashes can be enumerated. | Upstream hash examples do not override Spec§40's stricter prohibition on sensitive stable trace hashes. |
| [Collector resiliency](https://opentelemetry.io/docs/collector/resiliency/) | Finite queues and retries may drop observations; optional file_storage WAL persists queued data and recovers restart; loss remains possible. | Persistent queues add retained data. Durable audit and routine lossy telemetry need different policies. No exact config adopted. |
| [OTel tracing API](https://opentelemetry.io/docs/specs/otel/trace/api/), displayed spec 1.62.0 | One parent per span; links handle additional same/cross-trace causality. Context needs propagation; recording spans need ending. | Parent/links can express workflow causality; OTP supervision topology remains a separate relation. |
| [OTel Erlang/Elixir status](https://opentelemetry.io/docs/languages/erlang/), page modified 2026-01-27 | Traces Stable; metrics/logs Development; API/SDK/OTLP packages listed. | Package/signal maturity must be selected explicitly; no equal-maturity assumption. |
| [Erlang propagation](https://opentelemetry.io/docs/languages/erlang/propagation/), modified 2025-08-08 | HTTP instrumentation can inject/extract; documented defaults include tracecontext and baggage; manual context uses process dictionary. | Arbitrary process messages still need a BEAML adapter contract and tests. |
| [Baggage security](https://opentelemetry.io/docs/concepts/signals/baggage/), modified 2026-02-22 | Request propagation can expose data to third parties; baggage lacks built-in integrity; separate from attributes. | Neither authorization claims nor secret/PII should be accepted from baggage without independent policy/verification. |
| [PostgreSQL 18 row security](https://www.postgresql.org/docs/18/ddl-rowsecurity.html), §5.9 | Enabled RLS without matching policy denies; superuser/BYPASSRLS and normally owner bypass; whole-table operations have exceptions. | Tenant isolation must test actual runtime DB roles, not only policy existence. |
| [ClickHouse TTL](https://clickhouse.com/docs/concepts/features/operations/delete/ttl), mutable docs | Time-based delete/move/rollup; processing during merges, not immediate expiry. | Retention window and physical deletion deadline are distinct. Versioned deployment behavior untested. |
| [Amazon S3 expiration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html), mutable docs | Asynchronous expiration; versioned current expiry can leave noncurrent objects; separate lifecycle rules required. | Replay deletion needs version-aware verification. Amazon behavior is not proof for all S3-compatible products. |

**[Unknown]** No package versions, Collector distribution/components, storage engine schemas, deployment sizes, privacy controls, query benchmarks or deletion runbooks have been validated for BEAML. No infrastructure was provisioned or telemetry sent. For specification storage/retention requirements see [physical pp.13-14 §§39-45](engineering-spec-v0.5.md).

## Deeper protocol and operations coverage

Accessed 2026-11-05; [second selected capture](../../raw/research/security-observability/2026-11-05-deep-mechanisms.md). OTel general specifications display 1.62.0, OTLP 1.11.1 and semantic conventions 1.45.0; these are independent version axes. No language package/Collector distribution was executed.

| Primary section | Mechanism checked |
|---|---|
| [Tracing SDK: sampling/processors/batch](https://opentelemetry.io/docs/specs/otel/trace/sdk/) | Record-only differs from sampled; synchronous callbacks cannot be treated as free/background; bounded queue and flush timeout are explicit. |
| [Metrics SDK: cardinality](https://opentelemetry.io/docs/specs/otel/metrics/sdk/#cardinality-limits) | Limits apply to attribute combinations; synthetic overflow aggregation avoids silently losing all measurements. |
| [OTLP: partial success/failures](https://opentelemetry.io/docs/specs/otlp/) | Partial HTTP200 carries rejected counts and must not be retried as a whole request; transport receipt is not durable audit completion. |
| [Logs data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/), [naming conventions](https://opentelemetry.io/docs/specs/semconv/general/naming/) | Log body/attributes/resource/scope and timestamps/context are distinct; BEAML needs a typed mapping rather than arbitrary stringify. |
| [Error handling](https://opentelemetry.io/docs/specs/otel/error-handling/), [Collector configuration](https://opentelemetry.io/docs/collector/configuration/) | Runtime telemetry failures are contained; pipelines must enable components and preserve intended processor order. |
| [W3C Trace Context2021 recommendation](https://www.w3.org/TR/2021/REC-trace-context-1-20211123/#privacy-considerations) | Correlation/privacy/security remain relevant even without application payload. |
| [Postgres 18 WAL reliability](https://www.postgresql.org/docs/18/wal-reliability.html), [fsync/synchronous_commit](https://www.postgresql.org/docs/18/runtime-config-wal.html) | Durability depends on acknowledged commit policy and underlying storage assumptions; unsafe settings can invalidate assurances. |
| [ClickHouse row policies](https://clickhouse.com/docs/reference/statements/create/row-policy), [AWS object-version deletion](https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html) | Tenant access and actual object erasure have role/version-specific semantics; query filtering or GET404 alone is insufficient. |

The [operational walkthrough](../concepts/observability-and-replay.md#typed-event-mapping-and-sampling) now covers event/metric mappings, sampling, queue sizing, partial failure, durable audit and tenant/replay deletion probes. Those mappings and budgets are BEAML proposals derived from requirements, not tested defaults.
