---
id: source-replay-source-validation
kind: primary-source-research
status: selected-source-inspection
updated: 2026-11-05
---

# Replay source validation

Origin: official Temporal SDK source and Temporal, Kafka, Erlang, OpenTelemetry and Akka documentation. Access: 2026-11-05. [Selected capture](../../raw/research/replay-source-validation/2026-11-05-selected-notes.md), [provenance](../../raw/research/replay-source-validation/2026-11-05-provenance.json). Documentation is mutable; observed versions are recorded in the capture. Copyright remains with the upstream publishers. No runtime experiment was performed.

## Pinned replay mechanism

**[Verified]** Temporal TypeScript SDK revision `137e536c8d99c779600aae1d87e09319f09b978b` accepts history and workflow identity separately. Its history lacks the workflow ID. `runReplayHistory` uses a fake ID if none is supplied. A replay whose decisions depend on that identity needs the original identity too. [worker.ts lines 658–680](https://github.com/temporalio/sdk-typescript/blob/137e536c8d99c779600aae1d87e09319f09b978b/packages/worker/src/worker.ts#L658-L680)

**[Verified]** The SDK feeds validated histories to a replay worker and reports replay failures from eviction reasons. Replay workers suppress external sinks unless the sink opts into replay. That explicit opt-in means replay isolation still needs review. [History loop](https://github.com/temporalio/sdk-typescript/blob/137e536c8d99c779600aae1d87e09319f09b978b/packages/worker/src/worker.ts#L689-L725), [sink filter](https://github.com/temporalio/sdk-typescript/blob/137e536c8d99c779600aae1d87e09319f09b978b/packages/worker/src/worker.ts#L1904-L1913)

**[Verified]** Temporal determinism concerns the compatible workflow command sequence. Patch markers preserve version branches. Its recommended replay CI uses representative recorded histories. This does not establish arbitrary host-process reproduction. [Determinism](https://docs.temporal.io/workflow-definition#deterministic-constraints), [patching](https://docs.temporal.io/develop/typescript/workflows/versioning#patching-in-new-code), [replay testing](https://docs.temporal.io/develop/typescript/best-practices/testing-suite#how-to-replay-a-workflow-execution)

## Validation implications

**[Inference]** A REPLAY CAPSULE needs all inputs on which the chosen replay boundary depends, including contextual identities not present in its main history format. Exact command reproduction and full local-value capture are separate claims. The [main replay source note](event-sourcing-and-replay.md) records further activity-attempt omissions.

**[Proposal]** Validate unchanged-artifact replay before a COUNTERFACTUAL RUN. Compare decisions, errors and effect requests with the original REPLAY HISTORY. Never replace the original evidence with regenerated results. Deny external mutations in the replay harness, including optional sinks and foreign callbacks. Missing required evidence yields an explicit incomplete result.

**[Verified]** A worker can mutate an external service and crash before reporting success. Kafka output/offset coordination and target-side idempotency address different parts of that uncertainty. An unrecorded outcome cannot be relabeled as failure or absence of mutation. [Activity crash window](https://docs.temporal.io/activity-definition#idempotency), [Kafka delivery semantics](https://kafka.apache.org/41/design/design/#message-delivery-semantics)

**[Verified]** Erlang signal ordering is scoped to sender/destination pairs; it is not a global scheduler order. Ordinary OpenTelemetry batching may drop records. Neither supplies complete REPLAY HISTORY by itself. [Erlang signal delivery](https://www.erlang.org/doc/system/ref_man_processes.html#delivery-of-signals), [Logs SDK](https://opentelemetry.io/docs/specs/otel/logs/sdk/#batching-processor)

**[Unknown]** No BEAML replay harness, durable capture admission policy, sink isolation proof or completeness measurement exists. Selected upstream inspection does not validate those future components.
