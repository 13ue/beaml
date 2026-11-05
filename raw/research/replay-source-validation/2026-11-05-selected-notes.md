# Replay source validation supplement

Access: 2026-11-05. Coverage: selected official sections and one pinned SDK file, not a full audit. Paraphrases only. Copyright remains with Temporal Technologies, Apache Software Foundation, Ericsson AB and OpenTelemetry contributors. No framework was executed or selected.

## Temporal

- https://docs.temporal.io/workflow-definition#deterministic-constraints : replay needs a compatible Workflow API command sequence. External API calls, model calls and database operations belong outside the replayed workflow path. Time and random APIs must be replay-safe.
- https://docs.temporal.io/activity-definition#idempotency : an external action can succeed before its worker crashes without reporting success. A retry can repeat it. Target-side idempotency enforcement matters.
- https://docs.temporal.io/develop/typescript/workflows/versioning#patching-in-new-code : patch markers in history preserve the selected old/new branch during compatible replay.
- https://docs.temporal.io/develop/typescript/best-practices/testing-suite#how-to-replay-a-workflow-execution : replay histories from representative open and closed executions in CI; compatibility failures fail the check. This is a sampled compatibility check, not a proof for every possible execution.
- Pinned source: temporalio/sdk-typescript commit 137e536c8d99c779600aae1d87e09319f09b978b, commit timestamp 2026-11-05T16:36:17Z. Public API resolved main, then exact revision was fetched. packages/worker/src/worker.ts lines 658–680: runReplayHistory accepts a separate workflowId because history does not contain it; absent input becomes a fake ID. Lines 689–725: histories are validated, pushed into a replay worker, and eviction reasons produce replay results. Lines 1728–1736 and 1904–1913: replay workers suppress sinks unless configured callDuringReplay. That option is an isolation boundary, not a universal ban on all effects.

## Other reference boundaries

- https://kafka.apache.org/41/design/design/#message-delivery-semantics : external output and consumer position need coordinated storage; Kafka transactions alone do not atomically commit arbitrary external effects.
- https://www.erlang.org/doc/system/ref_man_processes.html#delivery-of-signals : displayed OTP29.1.2. Ordering is per sender/destination; delivery delay is unspecified and distribution loss is possible. This is not a total cross-process order. Priority-message reception may also alter mailbox placement relative to ordinary messages.
- https://opentelemetry.io/docs/specs/otel/logs/sdk/#batching-processor : displayed specification1.62.0. Full queues drop logs. Failed export batches are dropped. Ordinary logs cannot be assumed to be an exhaustive durable replay journal.
- https://doc.akka.io/libraries/akka-core/current/typed/persistence.html#event-handler : displayed2.10.24. Recovery reapplies events to state; the event handler must not perform side effects. Post-persist effects have separate crash and repetition limits.

## Research inferences

An execution history may need extra context such as workflow identity. Recreating its command sequence does not establish that every original local intermediate value was captured. A complete replay claim must state the boundary, dependencies, omitted data and isolation policy. These are proposed BEAML design obligations, not existing BEAML capabilities.
