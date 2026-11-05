---
id: concept-domain-modeling-contracts
title: Domain transitions, aggregate invariants and runtime consistency
kind: synthesis
status: proposed-not-implemented
updated: 2026-11-05
---

# Domain transitions, aggregate invariants and runtime consistency

**[Requirement]** BEAML's domain constructs are optional. Pure aggregate transitions can be analyzed; database atomicity, external effects and distributed consistency need runtime/integration guarantees. Command pre/postconditions and aggregate invariants require explicit semantics, not only annotations. [Spec p.4 §7](../sources/engineering-spec-v0.5.md)

**[Verified]** Evans's aggregate pattern assigns one root responsibility for an invariant boundary and separates synchronous internal consistency from cross-boundary coordination; a bounded context scopes model meaning. It is a modeling pattern rather than proof that a framework/database enforces the boundary. [Author reference, physical pp.9/23](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf), [coverage](../sources/domain-contracts-and-evolution.md)

## A local contract must say which states it relates

**[Verified]** Design by Contract distinguishes caller preconditions, supplier postconditions conditional on valid entry, entry-state values (`old`) and invariants at externally accessible stable boundaries. [Eiffel tutorial](https://www.eiffel.org/doc/eiffel/ET-_Design_by_Contract_%28tm%29%2C_Assertions_and_Exceptions)

**[Proposal]** Define a BEAML command relation with input state `s`, validated command `c`, successful next state `s'`, result/events and explicit error outcomes. A scoped preservation obligation is: if invariant I(s) and precondition P(s,c) hold and the transition succeeds, then I(s') and postcondition Q(s,c,s',result,events) hold. This is a proposed judgment, not a proof of the PDF invoice example or a guarantee that the transition terminates.

An invariant need not hold in every internal temporary while constructing a new immutable state; it must hold at the designated publication/commit boundary. Choose the meaning on error/cancellation too: unchanged state, explicit recovery state or no guarantee under a named foreign failure. A postcondition checked after irreversible external work cannot undo that work if it fails.

Contracts that read clocks, databases, randomness, principal policy or foreign functions are not automatically pure predicates. Capture those inputs explicitly, classify effects and state the supported static fragment. Unsupported/undecidable obligations remain UNKNOWN or require runtime checks; sampled examples remain TESTED. Untrusted browser/model data still needs boundary decoding/validation even if an internal caller is expected to honor a precondition. [Type/effect limits](types/refinements-and-effects.md), [product trust contract](product-contract.md)

## Separate decision, state evolution and commitment

**[Proposal]** A small domain layer can expose three concepts without choosing an event-sourcing framework:

1. Decide whether a validated command is allowed against a specific state/version; return domain rejection or a transition/events.
2. Evolve state with that transition/events and check the supported invariant/postcondition.
3. Commit through a versioned persistence adapter, then perform approved external effects under an explicit delivery protocol.

This is a design decomposition, not mandatory syntax or a required event-sourced storage model. Ordinary state persistence can use the same separation. The command's business rejection, validator failure, stale version, storage failure and uncertain commit are distinct outcomes.

**[Verified]** Akka's documented event-sourcing pattern separates command handling from event application; event application also runs during recovery, so external side effects there would repeat. Its persistence/side-effect APIs and single-writer assumptions have explicit limits. [Typed persistence](https://doc.akka.io/libraries/akka-core/current/typed/persistence.html)

**[Inference]** BEAML should learn that replayable state transitions must not silently invoke LLM/payment/email/network work. It does not need Akka or event sourcing. A BEAM process serializing its mailbox does not by itself serialize all writers to a database row or protect two aggregates from another application instance. [BEAM process boundaries](beam-runtime-and-interop.md)

## Runtime storage enforces different properties

**[Verified]** Ecto validation executes before repository operations while database constraints enforce storage integrity. Optimistic locking checks a row version and can raise a stale-update error. PostgreSQL row checks/NULL rules, unique/FK constraints, row locks and isolation levels address different conditions; serializable conflicts may require retry. [Ecto](https://ecto.hexdocs.pm/Ecto.Changeset.html#optimistic_lock/3), [constraints](https://www.postgresql.org/docs/18/ddl-constraints.html), [isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [row locks](https://www.postgresql.org/docs/18/explicit-locking.html)

**[Proposal]** Make an adapter state exactly which invariant it enforces: row-local validation, uniqueness, one aggregate version, multirow transaction or distributed protocol. A balance/total predicate over several rows cannot be made safe merely by doing a prior read and a pure calculation. Re-read/retry on version conflict and re-evaluate command preconditions against the new state; do not reuse a stale validated transition as if it were still applicable.

A transaction can fail after validation; the commit acknowledgement can also be lost. Define operation identity/deduplication and “unknown whether committed” handling before automatic retries. If state and outgoing messages must agree, use a reviewed transactional delivery/outbox-style protocol or another explicit mechanism; ordinary database commit and external HTTP are not one atomic operation. The protocol is a BEAML design question, not a feature inherited from Ecto/OTP.

Authorization is separate from state/schema validity. A command may be structurally valid and preserve the invariant while the principal lacks permission. Capture principal/tenant/purpose at the boundary and prevent cached witnesses from silently surviving an incompatible authorization/state/schema change. [IFC/authority](information-flow-security.md)

## Cross-aggregate workflows have failure states

**[Proposal]** Keep aggregate contracts scoped; cross-boundary workflows specify ordering, idempotency, retries, compensations and terminal/repair states. Compensation is another operation with its own failure/authorization contract, not time reversal. Eventual consistency must name the tolerated interim states and convergence/liveness assumptions. A compiler may check supported transition/effect rules; it cannot infer arbitrary distributed business correctness from the word `aggregate`.

## Evidence before declaring a domain feature done

**[Proposal]** Use a pure state-transition corpus for pre/postcondition/invariant examples and counterexamples; a sequential lifecycle reference model with precondition-preserving shrinking; and separate persistence integration races with stale versions, duplicate commands, commit failures, lost acknowledgements and recovery. Verify invalid inputs have zero domain effects. Record which guarantee is static, runtime-enforced, sampled or unknown; link evidence to exact contract/schema/build versions. [Generator/model mechanics](testing/generators-and-stateful-properties.md), [evidence manifests](static-architecture-and-evidence.md), [evolution](schema-and-api-evolution.md)

No aggregate runtime, transaction protocol or model checker is implemented here.
