---
id: concept-event-flows-backpressure
kind: architecture-proposal
status: proposed-not-implemented
updated: 2026-11-05
---

# Event flows, backpressure and replay boundaries

**[Requirement]** The user wants typed error replay around failures as a central BEAML goal.
**[Proposal]** Event transport should serve that goal without conflating delivery, domain commitment, observations and reproducible execution.
This page uses the [glossary](../../GLOSSARY.md) and three proposed [BOUNDED CONTEXTS](../planning/context-map.md).
The [source ledger](../sources/broadway-kafka.md) records selected primary evidence. Nothing here is implemented or benchmarked.

## Different jobs for processing, transport and history

**[Verified]** Broadway supplies concurrent pipeline stages. GenStage demand governs delivery between participating stages.
Kafka provides a retained partitioned log. Kafka transactions can coordinate offsets and Kafka outputs; external systems need additional cooperation.
[Broadway](https://broadway.hexdocs.pm/1.3.0/Broadway.html), [GenStage](https://gen-stage.hexdocs.pm/1.3.2/GenStage.html), [Kafka](https://kafka.apache.org/44/design/design/#message-delivery-semantics)

**[Proposal]** A broker stores transport records. An application event store defines authoritative domain history under explicit invariants.
A replay engine validates REPLAY HISTORY and reconstructs permitted execution under pinned contracts.
One storage system might support several roles, but its presence does not establish those contracts.

Kafka can be an optional transport or history component. Broadway can execute bounded consumption and batching.
Neither replaces the SEMANTIC MODEL, domain transactions or the typed replay design.
A compiler query does not need a Kafka round trip merely because it produces information.

## Flows and ownership

**[Proposal]** The tables define candidate policies, not existing guarantees. Storage names describe roles, not selected products.

| Flow | Semantic owner | Trust boundary | Storage and ordering | Privacy policy |
|---|---|---|---|---|
| Source changes and SEMANTIC FACTS | LANGUAGE/COMPILATION | Editor or AUTHORING AGENT input into compiler queries | Source revisions and derived cache. Results name their input version. New edits can supersede stale diagnostics. | Source and diagnostics can contain sensitive literals. Export only permitted projections. |
| Generated descriptors and EVIDENCE STATUS | LANGUAGE/COMPILATION → EXECUTION/OBSERVATORY | Versioned GENERATED ABI and evidence interfaces | Immutable build artifacts with exact identities. Consumers reject incompatible versions. | Descriptors expose only permitted metadata. Preserve unknown and scope information. |
| UI EVENT → COMMAND | EXECUTION / UI adapter | Browser strings into decoding, authorization and validation | Rejected drafts create no DOMAIN EVENT. Permitted TYPED ERROR capture follows policy. Accepted requests need a defined operation identity. | Avoid raw form capture by default. Retain only permitted ERROR CONTEXT references. |
| WORKFLOW RUN and PROVIDER ATTEMPT | EXECUTION | Provider transport into typed result checks | Authoritative lifecycle and REPLAY HISTORY. Capture causal links and relevant sequencing, not assumed global order. | Raw responses need explicit capture permission, access limits and retention. |
| Tentative DOMAIN EVENT → committed publication | Application domain hosted by EXECUTION | Pure transition into persistence and external transport | Commit state and publication intent together when required. Outbox delivery uses stable event identity and per-aggregate ordering. | A committed event still has SECURITY LABEL and recipient restrictions. |
| OBSERVATION EVENT | EXECUTION → OBSERVATORY | Policy-filtered runtime observation adapter | Bounded queues and query views. Arrival order can differ from execution order. Sampling and gaps remain visible. | Redact before egress. TRACE CONTEXT correlates; it grants no authority. |
| AUDIT RECORD | Action owner → OBSERVATORY audit boundary | Explicit durable policy and authorized audit ingestion | Dedicated durability contract. Required ordering and missing-record detection are stated per action class. | Restricted readers, independent retention and tamper-evidence rules. |
| REPLAY HISTORY and REPLAY CAPSULE | Originating context owns capture; OBSERVATORY presents authorized views | Recorded inputs into replay validation and controlled effect substitution | Versioned history plus CHECKPOINT and capture manifests where supported. Kafka offsets are only transport positions. | CAPTURE COMPLETENESS exposes omissions. Deletion or denied access can make replay unavailable. |

| Flow | Completion or acknowledgement | Backpressure and overload | Error, retry and replay policy |
|---|---|---|---|
| Compiler changes/results | Query completes for a named source version. Cache insertion is not source acceptance. | Coalesce obsolete edits. Bound pending work and cancellation. | Recompute derived facts. Report compiler failures separately from invalid source. |
| Descriptors/evidence | Consumer accepts a supported artifact version. | Bound artifact loading and invalidate stale references. | Reject mismatch. Do not silently reinterpret old evidence with new rules. |
| UI input | Request accepted, rejected or outcome uncertain. | Limit admission and outstanding requests. | Invalid input causes no domain effects. Duplicate submission uses explicit idempotency rules. |
| Workflow/provider work | Persist the declared lifecycle outcome or durable continuation before delivery completion. | Bound active runs, provider calls, tokens, bytes and retries. | Distinguish transport failure, invalid result, cancellation and uncertain external completion. Replay uses recorded inputs, not implicit live calls. |
| Domain publication | Durable consumer effect or durable recovery handoff, according to its contract. | Outbox and consumer quotas expose backlog. | Duplicate delivery is expected. Preserve identity. Retry or reconcile uncertain effects before claiming success. |
| Routine observations | Best-effort policy outcome, including explicit drop. | Drop, sample or aggregate under policy; do not block business work indefinitely. | Export retry is bounded. Missing observations do not imply missing domain actions. |
| Required audit | Durable acceptance under the stated failure model. | Reject or defer the protected action if mandatory audit cannot be secured. | Policy chooses fail/hold behavior. A telemetry drop policy cannot be reused silently. |
| Replay capture | Required data and manifest are durable, or incompleteness is explicit. | Admission limits precede required capture. Optional capture can degrade only with recorded gaps. | No complete GROUND TRUTH claim from partial history. Replay refuses unsupported gaps or reports their effect. |

LANGUAGE/COMPILATION owns source, compiler and editing-session history. EXECUTION owns workflow and effect history.
OBSERVATORY owns its retained ingestion, transformation and projection facts. Shared formats or replay runners do not transfer that ownership.

The last two policies can affect availability. Their transaction and crash windows require design and fault tests.
An OBSERVATION EVENT or successful callback cannot certify durable domain commitment.
[Domain persistence](domain-modeling-and-contracts.md), [security and observability](observability-and-replay.md)

## The connector failure seam

**[Verified]** BroadwayKafka 0.7.1 acknowledges failed messages too. Its acknowledger combines successful and failed offsets.
Pending deliveries prevent offset advancement across earlier outstanding work. That mechanism tracks delivery completion, not application success.
[Failure contract](https://broadway-kafka.hexdocs.pm/BroadwayKafka.Producer.html#module-handling-failed-messages), [pinned acknowledger](https://github.com/elixir-broadway/broadway_kafka/blob/dedd507e72b90ba2ef231286be811bb14b522026/lib/broadway_kafka/acknowledger.ex)

**[Proposal]** Example: offset 42 fails validation, while offset 43 represents the next operation for the same aggregate.
Returning offset 42 as failed does not guarantee it will return later. Continuing with 43 might violate required business order.
A retry queue can also deliver 42 after 43. The application must choose its policy before enabling that path.

Three possible policies have different costs:

1. Continue after a durable rejection record when the domain permits skipping invalid input.
2. Persist a retry or quarantine record before acknowledgement, then enforce per-key sequencing in a durable application layer.
3. Stop processing that ordering scope until recovery completes, using a connector strategy that actually supports the required behavior.

The third policy is not obtained by merely returning a failed Broadway message.
A failure callback that logs, raises or loses its recovery write is not a durable handoff.
Broadway catches failure-callback crashes and internally marks messages failed. With this connector, that still enters acknowledgement.
`offset_commit_on_ack: false` changes commit timing; it is not a per-message negative acknowledgement.
[Callback failure](https://broadway.hexdocs.pm/1.3.0/Broadway.html#c:handle_failed/2)

The adapter must prove the write-before-ack path under its actual failure semantics.
If that cannot be established, change the adapter or durability design.
Treat this as an adapter-selection gate, not a configuration promise.

An alternative is durable input admission before dispatch, with application-owned pending work and retry state.
That design still needs tested write/ack/crash semantics and duplicate recovery.
It must not depend on the same unsafe failure callback for its only durable input copy.
Persisting the original input does not record later errors, provider outcomes or irreversible effect completion.
Those history writes have separate failure windows. A missing external response can remain an explicit unknown outcome.

A crash after durable handoff but before offset commit can redeliver the same record.
Use stable identity and deduplication where the effect requires it.
A lost response after a payment or provider call can leave its outcome unknown.
An idempotent Kafka producer does not deduplicate that external effect.
[Delivery windows](https://kafka.apache.org/44/design/design/#message-delivery-semantics)

## Ordering, rebalance and shutdown

**[Verified]** BroadwayKafka routes each assigned topic/partition consistently to processors and batch processors.
Its producer stops fetching during revocation and drains dispatched work before completing the revoke callback.
Graceful shutdown has a time budget. A hard crash cannot rely on draining.
[Pipeline guide](https://broadway.hexdocs.pm/apache-kafka.html), [pinned drain implementation](https://github.com/elixir-broadway/broadway_kafka/blob/dedd507e72b90ba2ef231286be811bb14b522026/lib/broadway_kafka/producer.ex#L259)

**[Proposal]** Choose a key from the business ordering requirement, such as aggregate identity.
One hot key can constrain throughput despite idle workers elsewhere.
More consumers than useful assigned partitions do not remove that ordering constraint.
Adding partitions requires a key-routing and mixed-version review before claiming order across the transition.

Do not start untracked asynchronous work inside a callback and return before its completion contract is met.
That would detach the business effect from acknowledgement and failure handling.
Batch size and timeout trade latency against write efficiency. Batch completion still needs per-record outcome semantics.
Test slow keys, partial batch failures, revoke during calls, commit rejection, forced shutdown and duplicate delivery.

## Bounded memory and catch-up

**[Verified]** GenStage tracks demand separately per producer. Broadway warns that producer concurrency can multiply internal queueing.
Larger connector fetches increase memory use. Demand is not a global bound on broker backlog or arbitrary application mailboxes.
[Demand](https://gen-stage.hexdocs.pm/1.3.2/GenStage.html#module-demand), [producer concurrency](https://broadway.hexdocs.pm/1.3.0/Broadway.html#module-producer-concurrency), [fetch options](https://broadway-kafka.hexdocs.pm/BroadwayKafka.Producer.html#module-fetch-config)

**[Proposal]** Budget records and bytes at every queue, including decompressed payloads, batches, active calls and replay capture buffers.
Reject oversized records before expensive decoding where possible. Preserve a typed rejection outcome without retaining forbidden payloads.
Per-node rate limits do not imply a fleet-wide provider quota.

Illustrative arithmetic, not a benchmark:

- With input rate λ and completed rate μ, backlog grows approximately by `(λ−μ) × duration` when λ exceeds μ.
- A backlog B drains in approximately `B / (μ−λ)` seconds when μ exceeds λ and capacity remains stable.
- At 1000 records/s input and 1500 records/s completion, 300000 records need about 600 seconds to drain.
- Retaining 10000 decoded records at 20KiB each uses about 195MiB for payload alone. Terms, copies and indexes add overhead.

These averages hide hot partitions, variable payloads and provider latency.
No finite catch-up time exists in this model when μ is at most λ.
Measure end-to-end latency, oldest record age, per-partition lag, bytes, GC, queue depth, retry rate and sink saturation.
Kafka documents separate fetch and commit positions. A low fetch lag can coexist with unfinished business work.
Its Java-client metric names are not automatically supplied by brod.
[Monitoring scope](https://kafka.apache.org/44/operations/monitoring/#consumer-monitoring)

## Retained-log replay is only one input to typed replay

**[Verified]** Retention and compaction can remove records. Byte retention applies per partition; time retention does not guarantee indefinite history.
Compaction can discard intermediate states. Expired tombstones can invalidate a late state reconstruction.
[Topic policies](https://kafka.apache.org/44/configuration/topic-configs/), [compaction](https://kafka.apache.org/44/design/design/#log-compaction)

**[Proposal]** An offset identifies a log position, not a complete CHECKPOINT, causal order or execution state.
REPLAY HISTORY needs the relevant TYPE/SCHEMA identities, code, permitted inputs, provider outcomes and effect results.
The error path needs recorded failure and cancellation decisions, not only successful DOMAIN EVENTS.
Payload omissions, sampling, failed capture and expired records affect CAPTURE COMPLETENESS.

A REPLAY RUN must preserve the original evidence and identify its own results.
A COUNTERFACTUAL RUN changes inputs, code or behavior; it cannot overwrite the original GROUND TRUTH claim.
The [typed replay design](typed-errors-and-replay.md) owns those semantics. Transport cannot upgrade an incomplete capture into complete evidence.
[Replay source limits](../sources/replay-source-validation.md)

## Small validation slice before scale

**[Proposal]** Start with one rejected UI EVENT, one validated COMMAND and one failed PROVIDER ATTEMPT.
Retain permitted ERROR CONTEXT and reconstruct the failure without live external effects.
Add one committed DOMAIN EVENT with duplicate delivery and an uncertain publication acknowledgement.
Show safe observations separately from required audit and replay capture.

Then add the chosen transport adapter and repeat crash/rebalance/overload cases.
Kafka becomes useful when independent consumers, retained replay or measured backlog requirements justify its operational cost.
There is no universal event-rate threshold. Neither Kafka nor Broadway is selected by this proposal.
