---
id: concept-generators-stateful-properties
title: Typed generators, shrinking and stateful properties
kind: synthesis
status: proposed-not-executed
updated: 2026-11-05
---

# Typed generators, shrinking and stateful properties

**[Requirement]** Deriving Arbitrary must generate values of the declared type/refinement; accepted shrinking steps preserve them. Unsupported/failed generation reports exhaustion rather than a pass. Model-based traces execute a reference model and SUT adapter, preserve preconditions while shrinking, and record seed/compiler/generator/minimal counterexample. Concurrent scheduler testing is a later explicit phase. [Spec pp.3–4 §6; p.10 §28](../../sources/engineering-spec-v0.5.md)

**[Verified]** Upstream mechanisms below are Proptest source inspection at `70cf37d46b7d83393b6ed94c611f8c52209f585d`, retrieved 2026-11-05; not a BEAML dependency selection or executed result. [Source provenance](../../sources/compiler-verification.md)

## Generation and shrinking form one domain contract

Proptest's Strategy creates a ValueTree; `current` exposes a candidate while `simplify`/`complicate` search for a smaller still-failing example. Range strategies keep their allowed range while shrinking. A domain is more than the host language's storage type: positive/nonzero integers, sorted lists, a validated nominal ID or a dependent pair can require a custom construction/shrink relation. [Generation](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/tutorial/strategy-basics.md), [shrinking](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/tutorial/shrinking-basics.md)

**[Proposal]** For a BEAML type/refinement generator, expose a generated value plus a reproducible construction path; a shrink candidate is accepted only if its declared type/refinement holds and the failure still reproduces. Keep a deterministic simplification order and budget. “Minimal” means no smaller failing case found under that shrinker/budget, not a globally least counterexample.

| Type family | Proposed constructive strategy | Shrink obligation |
|---|---|---|
| Bounded scalar/interval | Draw directly in valid interval; include boundaries | Stay inside interval; avoid invalid zero/divisor transitions |
| Record/ADT | Choose inhabited variant and construct fields | Preserve variant invariants and dependent-field relationships |
| Length-indexed/const-sized container | Generate length from permitted const domain then elements | Shrink elements or length only with consistent type/index witnesses |
| Recursive type | Explicit size/depth/fuel distribution and reachable base cases | Reduce depth/size while preserving inhabitance/constraints |
| Refined pair/container | Construct from parameters that guarantee relation | Shrink parameters then reconstruct/recheck, not unrelated fields |
| Foreign/opaque/validated value | Reviewed fixture/adapter/generator capability | Preserve boundary witness; do not forge internal markers |

These are proposals until the corresponding type/refinement semantics are chosen. They do not solve arbitrary predicates or imply uniform sampling.

## Filtering, rejection and exhaustion

**[Verified]** Proptest distinguishes local and whole-case rejection. Rejection sampling can be slow or nonterminating without limits; configured limits abort. Rejected shrink candidates can prevent traversal to smaller valid cases. Its runner error enum distinguishes `Abort` from a failing test value. [Filtering tutorial](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/tutorial/filtering.md), [filter implementation](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest/src/strategy/filter.rs), [error type](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest/src/test_runner/errors.rs)

**[Proposal]** Prefer constructive strategies for intervals, constrained lengths and related fields. If bounded rejection/solver search is needed, report attempted/accepted/rejected cases and the exact exhaustion reason. Distinguish EMPTY (proved uninhabited under supported rules), UNSUPPORTED predicate, SOLVER_UNKNOWN/TIMEOUT, generation-budget exhaustion, test precondition rejection and actual counterexample. The final names/schema remain open; no category becomes property success automatically.

A solver-backed witness must still be decoded/validated according to the chosen type/logic semantics. Record solver version/options/assumptions; a timeout is not evidence the type is empty. Size bounds are test coverage limits, not mathematical bounds on the language. [Spec refinement/generator contract](../../sources/engineering-spec-v0.5.md)

## Recursive data needs a size policy

**[Verified]** Proptest's recursive tutorial illustrates unconditional recursion/rapid growth and uses a recursive combinator with explicit size parameters. These controls manage test construction, not semantic termination of user code. [Recursive strategies](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/tutorial/recursive.md)

**[Proposal]** BEAML derivation should detect impossible or unsupported recursive generator cycles; allocate size among branches, favor reachable base cases and expose distribution/coverage. Test empty/one-element/boundary nesting separately from random cases. An implementation can be type-correct while barely visiting a variant, so coverage classification should report variant/size/refinement buckets and reject counts.

## Stateful generation depends on the evolving model

**[Verified]** Proptest's reference interface supplies initial state, state-dependent transitions, application and preconditions; the SUT interface applies transitions and checks postconditions/invariants. The inspected sequential strategy rechecks preconditions during generation and shrinking. Its shrink operations include removing transitions, shrinking transition data and shrinking initial state. [Reference strategy](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest-state-machine/src/strategy.rs), [runner](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest-state-machine/src/test_runner.rs)

**[Proposal]** A BEAML lifecycle test should keep model state separate from SUT resources/IDs. Each generated command carries parameters; the reference determines if it is valid and the expected transition. After executing it on the SUT, compare observable result/error/events and check invariant. Cleanup must run after failure and between replay/shrink attempts so prior effects cannot contaminate the next case.

For example, deleting `approve` from a failing `approve; pay` trace makes `pay` invalid under the PDF invoice model. A shrinker must recompute state/preconditions, reject or repair the candidate under a specified policy, and rerun to verify the same failure. It must not report “pay rejected before approval” as a minimized violation of a property that only claimed behavior for valid commands. This is a non-executed illustrative trace, not implemented BEAML syntax. [Spec model](../../sources/engineering-spec-v0.5.md), [precondition checks](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest-state-machine/src/strategy.rs)

## Negative tests and concurrency are separate test domains

**[Proposal]** Keep valid-command model tests and malicious/invalid-input boundary tests as separate strategies/oracles. Invalid browser input should be generated deliberately to test zero domain effects; treating it as a discarded precondition would miss the security property. Similarly, provider failures, retries, timeouts and cancellation need explicit model outcomes rather than being silently skipped.

**[Verified]** The inspected Proptest state-machine support is sequential. Its API does not establish controlled concurrent scheduling or a linearizability checker. [Implementation/module](https://github.com/proptest-rs/proptest/tree/70cf37d46b7d83393b6ed94c611f8c52209f585d/proptest-state-machine/src)

**[Proposal]** A future concurrent runner must define happens-before/scheduler control, nondeterministic model acceptance, histories and shrinkable schedule evidence. BEAM task/process tests with timeouts are useful integration tests, but cannot be labeled exhaustive interleaving exploration. Database/distributed consistency require runtime assumptions outside a pure aggregate model.

## Replay needs the value as well as its seed

**[Verified]** Proptest persistence stores a generation seed; a changed strategy may produce another valid case from that seed. Thus source/tool versions matter. [Persistence contract](https://github.com/proptest-rs/proptest/blob/70cf37d46b7d83393b6ed94c611f8c52209f585d/book/src/proptest/failure-persistence.md)

**[Proposal]** Save original/minimized concrete input or command trace, seed/RNG algorithm, type/schema/refinement/generator/compiler/checker revisions, budgets/distribution, fixture responses and SUT/environment version. Store symbolic-to-runtime ID bindings safely if needed for replay. Redact or authorize sensitive test data; do not assume a fixture is public because a test generated it. Report successful cases, rejected cases, exhaustion, shrink attempts and the observed failing trace independently.

See [compiler verification/release evidence](compiler-verification.md) and [stream publication contracts](../structured-output-and-streaming.md). No generator/state-machine runner has been implemented or measured in this repository.
