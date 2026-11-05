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
