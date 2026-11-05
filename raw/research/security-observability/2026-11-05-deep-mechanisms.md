# Deep security and telemetry mechanisms - selected evidence

Accessed2026-11-05. Second capture; prior raw records unchanged. Selected researcher paraphrases and section metadata, not full upstream bodies. Copyright stays with publishers/authors. Examples in maintained concept pages are original proposed BEAML models, unexecuted. No security theorem audit/deployment test.

| Source / version | Sections actually inspected / observation |
|---|---|
| [Cornell Jif3.3.0 language](https://research.cs.cornell.edu/jif/doc/jif-3.3.0/language.html) | Labeled types, Authority and access control, Downgrading: value-label flow order/join, principal authority, confidentiality vs integrity release; runtime policy success/failure also must not leak. |
| [Cornell Jif3.3.0 label checking](https://research.cs.cornell.edu/jif/doc/jif-3.3.0/label_checking.html) | Revisited pc +normal/exception termination labels. Existing first capture covers this; no new full body retained. |
| [OTel tracing SDK](https://opentelemetry.io/docs/specs/otel/trace/sdk/), displayed1.62.0 | Sampling decision enum DROP/RECORD_ONLY/RECORD_AND_SAMPLE; synchronous processor callbacks should not block/throw; batch queue caps/drop, flush timeout. |
| [OTel metrics SDK](https://opentelemetry.io/docs/specs/otel/metrics/sdk/), displayed1.62.0 | Cardinality limits/Views/overflow aggregation. Unique attribute combinations drive series; overflow synthetic point preserves accounting under specified rules. |
| [OTLP](https://opentelemetry.io/docs/specs/otlp/), displayed1.11.1 | Full/partial success, retryable/nonretryable errors. Populated partial_success is not retried; HTTP200 can carry rejection counts. Server acceptance is a transport contract, not an arbitrary backend fsync guarantee. |
| [OTel error handling](https://opentelemetry.io/docs/specs/otel/error-handling/), displayed1.62.0 | Runtime library errors must not escape as unhandled exceptions; self-diagnostics separate. Initialization config failure is different. |
| [OTel logs model](https://opentelemetry.io/docs/specs/otel/logs/data-model/), displayed1.62.0 | Timestamp/ObservedTimestamp, TraceId/SpanId, Body/Attributes, Resource/Scope; event representation has signal-specific structure. |
| [OTel semantic naming](https://opentelemetry.io/docs/specs/semconv/general/naming/), displayed1.45.0 | Naming conventions are schema semantics, not permission for arbitrary dynamic attribute names. |
| [Collector configuration](https://opentelemetry.io/docs/collector/configuration/), mutable | Component configuration must be enabled in service pipelines; processor order controls processing order; auth/TLS configuration sections present. |
| [Collector agent deployment](https://opentelemetry.io/docs/collector/deploy/agent/), mutable | Local/alongside application collector sends to configured backends; local placement does not erase downstream trust choices. |
| [Collector security config](https://opentelemetry.io/docs/security/config-best-practices/), mutable | Auth/TLS, minimized surfaces and sensitive-data handling; exact distribution/components need explicit choice. |
| [W3C Trace Context](https://www.w3.org/TR/2021/REC-trace-context-1-20211123/), Recommendation2021-11-23 | Privacy/security consideration sections; context identifiers/state have correlation/security implications, no authentication guarantee. |
| [PostgreSQL18 WAL reliability](https://www.postgresql.org/docs/18/wal-reliability.html), §28.1 | Committed-state durability depends on forcing storage and hardware/cache behavior. |
| [PostgreSQL18 WAL configuration](https://www.postgresql.org/docs/18/runtime-config-wal.html), §19.5 fsync/synchronous_commit | Configuration distinguishes crash-consistency/durability; asynchronous commit may lose acknowledged recent transactions, fsync off can corrupt on crash. |
| [ClickHouse row policy](https://clickhouse.com/docs/reference/statements/create/row-policy), mutable | SELECT filtering policies scoped to users/roles; not recommended as general protection when users can modify tables or copy data. |
| [AWS deleting versions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html), mutable | Simple DELETE inserts marker in versioned bucket; GET404 does not prove erasure; versionId deletion permanently removes selected version. |

Coverage limits: OTel spec version and language-specific implementation maturity are different. Mutable docs not commit-pinned; no actual Erlang package/Collector/storage tuple selected. Existing raw capture contains sensitive-data/baggage/queue/RLS/TTL/lifecycle evidence, which should be read alongside this extension. Failed arXivHTML full-text fetch means pc/effects paper still abstract-only, not upgraded to full proof inspection.
