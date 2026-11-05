---
id: concept-typed-errors-and-replay
kind: architecture-proposal
status: requirement-backed-design-not-implemented
updated: 2026-11-05
---

# Typed errors and replay

**[Requirement]** The [2026-11-05 request R01](../sources/typed-replay-requirement.md) makes fully typed replay of the surrounding execution a central target. It expands the historical PDF's narrower fixture replay. The target includes failed or rejected work, not just successful DOMAIN EVENTS. The following design is a **[Proposal]**, not an implementation or a reduction of the target to logs. Terms are defined in the [glossary](../../GLOSSARY.md). [Primary mechanisms](../sources/event-sourcing-and-replay.md), [pinned replay implementation and source validation](../sources/replay-source-validation.md)

## GROUND TRUTH has an owner and a scope

| Owner | Authoritative evidence | What it cannot certify |
|---|---|---|
| LANGUAGE/COMPILATION | Source snapshot, selected language rules, exact compiler/dependency artifacts, semantic inputs and original diagnostics | The compiler itself is correct, or a runtime operation succeeded |
| EXECUTION | Committed domain state/history plus recorded command, decision and effect outcomes with causal identity | An unacknowledged external mutation did not happen; a provider statement is factually true |
| OBSERVATORY | Recorded observations and their capture policy/completeness | Missing execution data, domain commit, authorization, static proof or external world truth |

GROUND TRUTH means authoritative evidence for the named question. Keep original evidence immutable. A corrected compiler, migrated schema or changed fixture creates a new interpretation or COUNTERFACTUAL RUN. It does not rewrite what the original run observed. A recorded bad provider answer remains the original answer. A valid SCHEMA does not make that answer true. [Trust transitions](product-contract.md#trust-transitions-are-explicit)

A complete typed history can establish what the controlled execution observed and decided. It cannot establish every fact inside the provider, kernel, native library or external database. To include those boundaries, extend the capture contract and its trusted implementation. Do not silently call the smaller trace complete. [BEAM boundaries](beam/typed-language-boundaries.md)

## TYPED ERRORS survive every boundary

**[Proposal]** Define a versioned sum of errors. Example variants are language/parser/type/refinement failures, input decoding, policy denial, domain rejection, stale state, provider protocol, timeout, cancellation, persistence, uncertain external outcome, runtime failure, capture failure and replay divergence. Exact names and exhaustiveness belong to the originating LANGUAGE/COMPILATION, EXECUTION or OBSERVATORY contract. This is an illustrative algebra, not accepted BEAML syntax.

A TYPED ERROR record carries:

- Stable variant/code and typed details under an error-SCHEMA version. Expected/observed TYPE references and field paths are distinct from raw rejected values.
- Source/artifact/map identity, operation/WORKFLOW RUN/PROVIDER ATTEMPT identity, causal parent references and the boundary that reported the error.
- Structured causes and checked foreign-error translation. A foreign string stays classified untrusted detail, not a new semantic variant or public stack dump.
- Stage and outcome: rejected before effects, failed before commit, committed, or unknown. Record cancellation requested separately from cancellation acknowledged.
- Retry disposition and prerequisites: prohibited, safe under stated idempotency, reconcile first, or unknown. A Boolean `retryable` cannot encode all these cases.
- SECURITY LABEL, permitted ERROR CONTEXT references, policy version, CAPTURE COMPLETENESS and REPLAY CAPSULE reference where available.

Render a safe human message from the typed record. Do not erase the variant into `Exception(message)` between generated code, OTP, jobs and Observatory. Bound cause depth/cycles and detail sizes. Logging the typed record is still an egress operation. [IFC boundaries](information-flow-security.md)

**Worked failure.** A transport timeout after sending a payment-like tool request yields `outcome = unknown`, not `rejected before effects`. The typed error links the request identity and the last durable history entry. Replaying the timeout reproduces that observation without calling the tool. A production retry requires recipient-side idempotency or reconciliation; the REPLAY RUN cannot resolve the original uncertainty. [Distributed uncertain effects](beam/distribution-storage-and-upgrades.md#distribution-is-transport-plus-a-cluster-trust-domain)

## Capture the inputs that can change the result

**[Proposal]** A REPLAY CAPSULE has a manifest and authorized referenced objects. The manifest binds scope, tenant/principal/purpose policy, artifact identities, sequence bounds, initial state or CHECKPOINT, parent histories, typed error and CAPTURE COMPLETENESS. Integrity checks detect corruption or mismatch; hashes alone neither authenticate the original writer nor prove no entry was omitted. Sensitive content must not become a public stable hash or identifier.

### LANGUAGE/COMPILATION profile

Capture an immutable source tree and unsaved buffer versions; imports, generated interfaces and exact dependency artifacts; compiler/checker/backend/OTP/Elixir/target versions; feature flags and explicit nonsecret configuration inputs; SCHEMA capabilities and reviewed foreign manifests; source maps; diagnostics; and the invocation/query request. Capture permitted inputs through a narrow manifest. Do not inspect the shell environment, secret files or credential locations to build it.

A batch reproduction runs the exact toolchain and input snapshot. Compare typed diagnostics by code, semantic target, TYPE/OBLIGATION and versioned source range. Compiler crashes may occur before a well-typed program exists. The capsule must represent malformed bytes, unresolved names, partial CST/AST and parser recovery as such. It must not invent typed HIR for rejected syntax. [Compiler mechanisms](compiler-and-tooling.md), [Clang reproducer precedent](../sources/event-sourcing-and-replay.md)

An incremental reproduction also needs ordered edits, document versions, query requests/cancellation and dependency/cache identities. Capture the starting snapshot and relevant persisted cache format/provenance where policy permits. A reproducible stale-cache failure may disappear in a fresh compiler. Compare incremental and fresh results, retaining both outcomes and invalidation evidence. A snapshot alone is incomplete for this fault. If worker interleaving affects a compiler bug, record/control that scheduling boundary or report it unsupported. [Query identity](compilers/incremental-compilation-and-source-identity.md)

**Worked example.** Start at source revision A. An unsaved Unicode edit changes a declaration at document version 7. A query issued for version 6 completes late. Record edit/query/response identities and the stale-publication decision. A fresh version-7 build can pass while the original incremental session returned the wrong location. Reproduce the edit sequence before minimizing the case. Keep the original capsule and mark a reduced test as a derivative, not replacement evidence.

### EXECUTION profile

Capture the accepted or rejected COMMAND envelope, tenant/principal/purpose references, policy/schema versions, state version and decision inputs. Capture successful DOMAIN EVENTS and commit acknowledgments separately from intended transitions. Record rejected commands too; event-sourced committed state alone omits the path to many errors. [Domain commitment](domain-modeling-and-contracts.md)

Treat every nondeterministic boundary as an input to deterministic replay: clock readings/timer firings, random/UUID results, external reads, tool/provider requests and observed outcomes, delivery order where code can observe it, retries, cancellations and process exits. A seed can replace recorded random outputs only if algorithm/version/call ordering and relevant behavior are fixed. Record decision branches if required for diagnosis, and verify them against recomputation rather than silently trusting inconsistent claims.

For a PROVIDER ATTEMPT, retain request descriptor and approved payload reference, provider/configuration version, operation/attempt identity, response status and allowed headers, ordered raw chunks if parsing depends on their boundaries, parser revisions/partial outputs, final validation and errors. Record disconnect/cancel/timeout observations and durable terminal status. Final text alone may not reproduce a partial-parser or publication bug. Do not merge retry streams. If the provider retries internally, capture that boundary or report its internal attempts unknown. [Stream semantics](structured-output-and-streaming.md)

This profile does not require storing every pure local variable. Recompute pure typed values from captured inputs and pinned semantics. If full surrounding inspection requires intermediate values that cannot be deterministically recovered, capture those values under policy or mark the requested scope incomplete. Stacks and pids are observations; stable logical identities must survive a different REPLAY RUN lifetime.

**[Verified]** Temporal's managed history and command comparison illustrate deterministic workflow reconstruction. Its ordinary activity history does not retain every intermediate retry as a full attempt trace. BEAML's requested attempt/chunk coverage therefore needs an explicit contract beyond assuming a default workflow engine history is enough. [Selected primary sources](../sources/event-sourcing-and-replay.md)

### OBSERVATORY profile

Routine OBSERVATION EVENTS stay sanitized, bounded and potentially sampled/lost. The durable REPLAY HISTORY is a separate authorized channel with its own admission, storage and acknowledgment policy. Link the two through permitted opaque references. Missing a sampled span must not remove a required effect outcome from the journal. An AUDIT RECORD of access or release is distinct from the full execution data required for replay. [Observation versus audit](observability-and-replay.md#durable-security-audit-is-a-separate-transaction-problem)

### OBSERVATORY reproduces its own failures

**[Proposal]** OBSERVATORY also owns failures in ingestion, decoding, redaction, transformation, projection, query and export. Its REPLAY CAPSULE is not merely a link to an EXECUTION capsule. Capture authorized original ingest records with transport/decoder/schema versions; exact transform and policy artifacts; routing identity; relevant projection CHECKPOINT, deduplication state, aggregation/window configuration and recorded clock/watermark inputs; storage/export request and observed response fixtures. Preserve which input prefix was durably accepted. Original records can be schema-invalid: use a typed untrusted fixture and decoding TYPED ERROR. Current access policy still gates replay.

Run the original decoder/transform/projection into an isolated scratch view. Substitute recorded storage/export responses; never send a reproduction batch to the production Collector or mutate the original query view. Compare typed rejection, projected state and output decisions. The authority is the retained ingestion/projection history, not a claim to recreate the underlying world's execution. Rebuilding a view and reproducing its failed write are different operations.

**Worked partial-acceptance failure.** A sanitized batch is sent downstream. The recorded response accepts only part of it; the original adapter incorrectly classifies the whole batch as successful. Capture the authorized batch, response including rejected count, adapter/policy versions and relevant checkpoint. A REPLAY RUN feeds the same response to the original adapter and reproduces the incorrect typed delivery state. A fixed adapter is a COUNTERFACTUAL RUN. If the protocol does not identify which records were rejected, preserve that uncertainty; do not invent per-record outcomes. The [OTLP partial-success rule](observability-and-replay.md#queue-arithmetic-and-failure-transitions) also prohibits retrying populated partial success wholesale.

A different case is a malformed input rejected before durable admission. Reproduction requires the allowed original bytes, decoder version and rejection record. If a dropped/sampled input was never retained, a projection rebuild cannot recover it. If a storage failure prevented both input and error recording, report an unavailable interval from surviving evidence. A failed capture path cannot guarantee recording its own loss. Bound view-rebuild claims by retained inputs, state, versions and clock/window coverage.

The three contexts own their original histories. A shared REPLAY CAPSULE format or runner protocol does not make EXECUTION the authority over compiler source or Observatory projection semantics. Cross-context capsules reference each owner and its versioned contract. No fourth universal context is required.

## Capture before the error and name the crash window

**[Proposal]** An error trigger can retain a bounded pre-error buffer plus a post-error window. That is useful for diagnosis. It cannot promise complete history if older inputs were evicted, the process crashed before flushing, or the error signal was never received. Advertise the buffer's actual temporal/causal coverage and lost counts.

For required full replay, durably admit the initial state and each required nondeterministic outcome before dependent execution may forget it or publish derived output. Define the exact acknowledgment boundary. If mandatory capture is unavailable or forbidden, reject admission into the promised reproducible mode or report the execution explicitly incomplete. Whether ordinary business execution may continue is a product/policy decision. This stricter journal policy must not accidentally block business work through ordinary telemetry failure.

There remains an external-effect window: durable intent → external effect → durable observed result. A crash between effect and result can leave unknown outcome. No local append operation atomically commits an arbitrary provider. Use stable operation identity and reconciliation, and preserve the unknown. A gap-free workflow decision history is not automatically a gap-free provider-side history.

Candidate CAPTURE COMPLETENESS states are `complete for declared scope`, `partial`, `forbidden required data`, `lost/corrupt`, and `unknown`; candidate replay outcomes are `matched`, `diverged`, `blocked by missing evidence`, and `unsupported boundary`. These are proposed data values. A successful replay does not upgrade partial capture to complete. Verify manifest coverage against required effect/source IDs, sequence continuity, parent links, fixtures and checkpoint boundaries. Continuity checks need a trusted append protocol to distinguish deliberate truncation from a naturally short run.

## Typed invalid input stays invalid

**[Proposal]** Persist a discriminated fixture: authorized raw/untrusted representation with encoding/SCHEMA expectation, or parsed value, or a versioned VALIDATED VALUE plus validator evidence. Persist errors and rejected paths without promoting a failing payload to `Validated<T>`. The container can be fully typed while its payload is explicitly `untrusted bytes` or `rejected input`. Full typing does not mean every captured value passed domain validation.

**Worked example.** A UI EVENT supplies a negative amount and a forged nominal ID. The capsule identifies raw field encodings, decoder/schema version, rejection path and zero-effect outcome. A REPLAY RUN feeds the same allowed raw input to the same decoder. Constructing an `Invoice` or forging a validated marker would bypass the failing boundary and invalidate reproduction. If policy removes the original field, a synthetic replacement is a COUNTERFACTUAL RUN and the original remains unreproducible for that field. [UI boundary](ui/typed-forms-and-events.md#worked-invalid-to-no-effects-example)

## A REPLAY RUN is isolated and checks divergence

**[Proposal]** The runner follows these steps:

1. Authorize capsule access under current tenant/purpose rules. Include contextual identities required by code, even if the history format omits them; the [pinned Temporal SDK example](../sources/replay-source-validation.md#pinned-replay-mechanism) requires workflow identity separately. Review optional callbacks/sinks as external-effect paths. Check artifact integrity, availability, versions and CAPTURE COMPLETENESS before running.
2. Load the exact toolchain and initial snapshot/CHECKPOINT into a separate execution boundary. Install a replay EFFECT interpreter. Deny live network, production database writes, emails, payments, model calls and credential access.
3. Match the next requested effect to its recorded identity, typed arguments, attempt and causal position. Return its recorded authorized outcome. Missing, unexpected, reordered or incompatible effects yield typed divergence, not a live fallback.
4. Recompute pure transitions, parsing, validation and typed diagnostics. Compare required command/state/publication/commit-intent outputs. Consume recorded clock/random/timer and cancellation inputs. Preserve the original unknown outcomes.
5. Report first divergence, expected/actual types and source, consumed history range and remaining gaps. Store the derivative result separately from original evidence. Audit access without copying payload into audit metadata.

There is no universal total order across unrelated processes. Capture the order of causally relevant inputs at the controlled boundary; record selected interleavings where races matter. A deterministic interpreter or constrained scheduler can reproduce that selected scope. Arbitrary BEAM scheduler, NIF, kernel and distributed races need additional instrumentation and a declared model. Unsupported concurrency remains explicit; this is an unresolved capability to build, not a reason to drop R01. [OTP process order](beam/processes-messages-and-otp.md)

The [flow map](event-flows-and-backpressure.md) records an important delivery gate: standard BroadwayKafka failure acknowledgment is not a durable retry guarantee. Do not promise complete capture or no loss without a validated admission/acknowledgment design.

Kafka retained-log consumption replays records to a consumer. Event-sourced recovery folds committed DOMAIN EVENTS. A REPLAY RUN reconstructs typed execution using captured boundary outcomes. A production retry performs new work and may cause new effects. A COUNTERFACTUAL RUN changes inputs/code/policy. Label these operations separately in APIs and UI. [Event-sourcing sources](../sources/event-sourcing-and-replay.md)

Report three independent results: CAPTURE COMPLETENESS, replay-engine execution status, and original-error reproduction. A runner can finish successfully while the original error is absent. A runner can reproduce a typed rejection exactly; that is a successful reproduction of an application failure. A divergence failure is neither result. Compare variant, source/obligation, causal position and required typed details under a declared equality contract; do not match display strings alone.

## Event sourcing is a per-context decision

**[Proposal]** LANGUAGE/COMPILATION keeps authored source and immutable build inputs authoritative. The semantic cache is derived. Recording edits and query history helps reproduce incremental faults; it does not require event-sourcing every compiler pass. Preserve initial inputs when starting a new history segment.

EXECUTION may choose committed DOMAIN EVENTS as application state authority. That decision has not been made. Ordinary database state plus versioned transactional history/outbox is another candidate. The execution/effect REPLAY HISTORY supports reproduction; it is not automatically the business source of truth. A rejected command can belong in replay evidence without becoming a committed DOMAIN EVENT.

OBSERVATORY maintains projections of authorized retained inputs. Rebuild is possible only for the retained scope. Sampled/lost observations cannot reconstruct a missing run. If ingestion or capture itself fails, expose its last durable position and an unavailable/unknown interval through an independent health path where possible. A crash can prevent even that record. No finite journal can recursively guarantee a durable record of every failure of the journal and its storage; define the fault model and verification boundary.

## Acceptance by context

**[Proposal]** These checks are unexecuted. A shared test should cross all three contexts.

| Scope | Synthetic failure and captured inputs | Required evidence |
|---|---|---|
| LANGUAGE/COMPILATION | Malformed source plus an unsaved edit causing stale incremental diagnostics | Reproduce typed parser/recovery diagnostics or compiler failure with original artifacts/edit/query versions; compare fresh versus incremental and reject stale output |
| EXECUTION | Effect intent persisted, tool mutation possible, worker dies before durable result | Original TYPED ERROR keeps outcome unknown; replay returns the recorded unknown without tool IO; reconciliation is a separate authorized operation |
| OBSERVATORY | Malformed ingest record or partial acceptance under pinned decoder/transform/policy, plus projection/checkpoint/dedup/window state and response fixtures | Reproduce typed rejection or original delivery/projection defect in a scratch view with no live export; missing input blocks complete reproduction; test journal outage and denied capsule access separately |
| Cross-context | Invalid UI input; then separate valid command with streamed provider chunks and a recorded validation failure | Preserve raw/parsed/validated distinction, original SCHEMA WITNESS and source IDs; replay chunks in original order; observe same typed failure; no provider/domain effects during replay; missing chunk gives blocked/diverged result |
| Infrastructure boundary | Capture process or storage crashes before acknowledging an append | Verify actual durable prefix and admission/publication behavior; no invented acknowledgment or recursive no-loss guarantee |

## Versions and privacy are part of reproducibility

**[Proposal]** Preserve original writer SCHEMA, decoder/validator/SCHEMA WITNESS, artifact and policy identities. Prefer running original supported artifacts in an isolated boundary for exact reproduction. If conversion is necessary, record an explicit versioned upcaster with input/output evidence. A new default, changed refinement, redaction or decoder can alter behavior. Report that as migrated interpretation or COUNTERFACTUAL RUN; never relabel it exact original replay. A CHECKPOINT binds state version and history position; event deletion and checkpoint retention need a reviewed recovery contract. [Evolution](schema-and-api-evolution.md)

The user target does not permit secret collection. This authoring task reads no secret files, secret names, key material or operational credentials. A future capture design must also prohibit secrets by construction and classify permitted sensitive payloads before persistence. Keep tenant authorization, encryption, access audit, expiry, deletion, backup/replica behavior and consent revocation explicit. Encryption is not collection permission. Destroyed/expired/forbidden necessary data makes exact replay unavailable; expose the loss of capability. De-identified replacements cannot prove reproduction of a data-dependent original failure. [Retention/deletion](observability-and-replay.md#tenant-isolation-deletion-and-replay-runbook-shape)

## First validation evidence and remaining decisions

**[Proposal]** Start with local synthetic permitted fixtures. Demonstrate typed parser/type/refinement rejection, a stale incremental edit, a provider stream revision failure, duplicate delivery, timeout with unknown external outcome, cancellation race, and journal crash-before/after-ack. For each case, preserve original artifacts; replay without live effects; compare typed outputs; remove or corrupt one required entry and require an explicit gap/divergence result. Add tenant-denial, policy revocation, expired fixture and version-mismatch cases. Assert invalid inputs cause zero domain effects. These are proposed acceptance checks, not executed tests or historical PDF gates.

**[Unknown]** Required capture scope, journal transaction protocol, observation granularity, concurrency model, cost/latency budget, completeness proof, codec/storage/retention choices and replay artifact support remain open. No Kafka, Broadway, Temporal, event-sourcing framework or deterministic VM is selected by this page. [Build readiness](../planning/build-readiness.md), [open decisions](../planning/specification-gaps.md)
