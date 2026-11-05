# Selected primary evidence capture - 2026-11-05

Coverage: researcher-authored paraphrases of selected inspected sections, not complete upstream documents or executable configurations. Captured by browser read, 2026-11-05. URLs below identify upstream evidence; mutable pages need rechecking before implementation. Copyright remains with named publishers/authors. No upstream license is applied to this repository. No substantive verbatim quotations are retained. Researcher notes and BEAML proposals are recorded in wiki synthesis rather than presented as upstream behavior.

## ifc-dlm
- Publisher: Cornell Jif project; documentation version 3.3.0.
- URL: https://research.cs.cornell.edu/jif/doc/jif-3.3.0/dlm.html
- Sections inspected: Principals; Labels; Label syntax.
- Selected evidence: Jif models principals/delegation and separates confidentiality and integrity policies. Labels support lattice joins/meets. This is a concrete reference model, not BEAML's defined lattice.

## ifc-checking
- Publisher: Cornell Jif project; documentation version 3.3.0.
- URL: https://research.cs.cornell.edu/jif/doc/jif-3.3.0/label_checking.html
- Sections inspected: Program counter labels; Normal and exceptional termination; Declassification.
- Selected evidence: pc summarizes control-flow sensitivity. Exception occurrence and normal completion also have labels. Confidentiality downgrades are declassification; label-checking includes authority constraints.

## ifc-paper
- Authors: Andrew C. Myers and Barbara Liskov.
- Title: Protecting Privacy using the Decentralized Label Model.
- URL: https://www.cs.cornell.edu/andru/papers/iflow-tosem.pdf
- Coverage: first-page abstract/publication-permission notice and selected indexed discussions, not full-paper review.
- Selected evidence: decentralized ownership/authority enables controlled declassification; Jif demonstrates static checking. Paper copyrighted by ACM; only attributed summary retained, no PDF redistribution.

## ifc-pc-effects
- Authors: Andrew K. Hirsch and Ethan Cecchetti.
- Title: Giving Semantics to Program-Counter Labels via Secure Effects.
- URL: https://arxiv.org/abs/2010.13191v2
- Version: v2, 10 December 2020; PACMPL 5 POPL Article 35 (2021), DOI 10.1145/3434316.
- Coverage: abstract and bibliographic metadata, not proof/full-paper review.
- Selected evidence: framework relates pc labels to effect semantics, including state, exceptions and nontermination; lower-bound folklore is qualified, not universal.

## beam-sensitive
- Publisher: Erlang Ecosystem Foundation Security WG.
- URL: https://security.erlef.org/secure_coding_and_deployment_hardening/sensitive_data.html
- Version: mutable page accessed 2026-11-05.
- Sections inspected: General; Erlang; Elixir; Background; Wrapping; Stacktrace pruning.
- Selected evidence: sensitive values can surface in arguments/stacktraces, logs, introspection and dumps. Suggested mitigations include Inspect/format_status controls, private ETS, sensitive process flag and argument pruning. Immutable BEAM values complicate erasure.

## otel-sensitive
- Publisher: OpenTelemetry project.
- URL: https://opentelemetry.io/docs/security/handling-sensitive-data/
- Version: mutable docs accessed 2026-11-05.
- Sections inspected: Your responsibility; Data minimization; Protecting sensitive data; hashing limitations.
- Selected evidence: implementer must classify sensitive data and review instrumentation; Collector offers filtering/removal/allowlisting/transforms. Small predictable input hashes can be reversed by enumeration; hashing is not assured anonymization.

## otel-resiliency
- Publisher: OpenTelemetry project.
- URL: https://opentelemetry.io/docs/collector/resiliency/
- Version: mutable docs accessed 2026-11-05.
- Sections inspected: Sending queue; Persistent storage; Circumstances of data loss.
- Selected evidence: finite in-memory queues/retry limits can lose data. file_storage WAL persists queued observations and can recover after restart, but disk/retry failures still lose data. These are tunable mechanisms, not end-to-end durability proof.

## otel-trace-api
- Publisher: OpenTelemetry project.
- URL: https://opentelemetry.io/docs/specs/otel/trace/api/
- Version displayed: OTel specification 1.62.0 (accessed 2026-11-05).
- Sections inspected: Span creation/parent/context; Specifying links; Link; SpanKind.
- Selected evidence: a span has at most one parent; links represent other causal relations within/across traces. Parent context needs propagation; created recording spans need ending. Links are not OTP supervision semantics.

## otel-erlang
- Publisher: OpenTelemetry project.
- URL: https://opentelemetry.io/docs/languages/erlang/
- Version: mutable docs, modified 2026-01-27; accessed 2026-11-05.
- Sections inspected: Status and Releases; Version support; Repositories.
- Selected evidence: status table says traces Stable, metrics/logs Development. Lists API/SDK/exporter packages and stated baseline Erlang23+/Elixir1.13+. Specific package support must be pinned separately.

## otel-propagation
- Publisher: OpenTelemetry project.
- URL: https://opentelemetry.io/docs/languages/erlang/propagation/
- Version: mutable docs, modified 2025-08-08; accessed 2026-11-05.
- Sections inspected: Automatic and Manual context propagation.
- Selected evidence: supported framework instrumentation injects/extracts context; default documented text propagators are W3C trace context and baggage. Manual API reads/writes context from process dictionary; this does not establish arbitrary OTP message propagation.

## otel-baggage
- Publisher: OpenTelemetry project.
- URL: https://opentelemetry.io/docs/concepts/signals/baggage/
- Version: mutable docs, modified 2026-02-22; accessed 2026-11-05.
- Sections inspected: Baggage security considerations; Baggage is not the same as attributes.
- Selected evidence: baggage may propagate to unintended third parties in request headers and has no built-in integrity checks. Baggage is a separate store; attribute copying is explicit.

## postgres-rls
- Publisher: PostgreSQL Global Development Group.
- URL: https://www.postgresql.org/docs/18/ddl-rowsecurity.html
- Version: PostgreSQL18 chapter5.9; current redirect resolved to18 on access 2026-11-05.
- Sections inspected: Row Security Policies introductory semantics.
- Selected evidence: enabled RLS without matching policy defaults deny; superusers/BYPASSRLS always bypass, owners normally bypass unless forced. RLS has whole-table exceptions and is not a universal tenant-security proof.

## clickhouse-ttl
- Publisher: ClickHouse.
- URL: https://clickhouse.com/docs/concepts/features/operations/delete/ttl
- Version: mutable docs accessed 2026-11-05; older guides/developer/ttl URL redirects here.
- Sections inspected: Overview; Triggering TTL events.
- Selected evidence: TTL can delete/move/roll up rows/columns. Expiry processing happens during merges rather than at the exact deadline.

## s3-expiry
- Publisher: Amazon Web Services.
- URL: https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html
- Version: mutable S3 guide accessed 2026-11-05.
- Sections inspected: Expiring objects; versioning implications; expiration delay.
- Selected evidence: nonversioned deletion is asynchronous; versioned expiry can create delete markers without deleting old versions. NoncurrentVersionExpiration is separate; object lock/replication status can affect action. This evidence covers Amazon S3, not every S3-compatible implementation.
