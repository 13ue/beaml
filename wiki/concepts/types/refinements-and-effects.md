---
id: concept-refinements-effects
kind: mechanism-guide
status: researched-and-proposed
updated: 2026-11-05
---

# Refinement obligations and effect checking

**[Requirement]** BEAML starts with constant/interval refinements, explicit checked conversions for unsupported predicates, effect sets/subset checking and pure functions unable to call effects. Handler dictionaries come first, algebraic continuations later. [Spec S03/S04/S20](../../sources/engineering-spec-v0.5.md). Examples are unexecuted candidate rules, not settled syntax.

## Turn a refinement subtype into a validity question

**[Verified]** [Jhala/Seidel/Vazou's tutorial](https://ucsd-progsys.github.io/lh-workshop/02-refinements.html) checks refinement subtyping through logical implication. [Liquid Types](https://goto.ucsd.edu/~rjhala/papers/liquid_types.html) combines type inference with predicate abstraction over qualifiers, rather than making every predicate decidable.

**[Proposal]** For candidate `Nonnegative={v:Int|v>=0}`, checking `x+1:Nonnegative` under Γ containing x>=0 produces `x>=0 => x+1>=0`. Check satisfiability of its negation, `x>=0 && x+1<0`. Over mathematical integers that is unsatisfiable, so the obligation is discharged under those assumptions. If BEAML Int wraps at a machine bound, the translation is wrong: maximum x can overflow. Choose integer semantics first, then the solver theory (unbounded Int, bitvectors, Decimal model, or explicit overflow checks).

To show `x-1:Nonnegative`, the negation has a model x=0. The model is a counterexample to this obligation; an error should point to the subtraction and missing precondition, not merely say “solver failed.” In an interval-only checker the same reasoning can happen without SMT: x∈[0,+∞) gives x+1∈[1,+∞), but x-1∈[-1,+∞) is insufficient.

**[Verified]** [SMT-LIB2.7, check-sat/reason-unknown](https://smt-lib.org/papers/smt-lib-reference-v2.7-r2025-07-07.pdf) separates sat/unsat/unknown. **[Proposal]** Map unsat of the correctly encoded negated VC to supported static evidence; sat to a checked counterexample; unknown/timeout/unsupported translation to UNKNOWN. Do not treat a model from an unknown result as a validated source counterexample without replay. Record predicate/assumption/checker/solver version and artifact identity; stale solver cache keys cannot authorize a new schema/policy.

## Checked conversion is an actual branch

**[Proposal]** Boundary `check_nonnegative(x)` must return `Result<Refined<Int,P>,ValidationError>` and run P before creating the refined wrapper. The success branch has x>=0; failure remains a normal declared outcome. An unchecked host struct constructor cannot create that witness. For an unsupported pure predicate such as `business_rule(x)`, choose an explicit runtime checker only if its termination/effect/error contract is defined; “the solver cannot prove it” does not automatically make arbitrary code safe to run during compilation.

Refinement generator derivation and shrinking must preserve the same predicate semantics; rejecting exhausted generation as a pass would produce false confidence. [Property and generator mechanisms](../compiler-and-tooling.md#properties-worth-testing) and future focused testing pages are complementary; source proofs and sampled executions retain distinct statuses.

## Effects are latent in functions, accumulated at calls

**[Proposal]** A candidate judgment `Γ⊢e:T!E` tracks immediate evaluation effects. A function value has a latent effect `A -{E}-> B`; creating a closure may be pure, calling it incurs E. For sequencing two calls use a union of effects; for a branch include condition and both possible branch effects. An empty body effect can be used in a wider declared allowance, but a network call cannot be accepted under pure merely because its output is discarded.

```text
map(f, xs)                -- schematic higher-order call
f : A -{ε}-> B
map : (A -{ε}-> B, List<A>) -{ε}-> List<B>
```

If map's type dropsε, passing an LLM-calling callback hides a real effect. A v1 without effect polymorphism can require an explicit conservative effect set or disallow unsupported higher-order cases. With polymorphism it needs effect variables, row/set constraints and a defined duplicate/idempotence model. [Leijen's effect-row paper2014](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/paper-20.pdf) demonstrates one inference design; it is not BEAML's automatically selected effect algebra.

## Dictionaries versus algebraic handlers

**[Requirement]** The spec's initial handler dictionaries can supply operations explicitly. **[Proposal]** `fetch(ctx,request)` can call `ctx.network.fetch` with a declared effect and cleanup contract. A fixture dictionary supplies recorded responses; a production dictionary supplies transport. Passing the dictionary is evidence of available capability, not proof that its foreign implementation obeys an assumed effect/taint manifest.

**[Verified]** [Leijen's handler compilation2016](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/08/algeff-tr-2016-v3.pdf) gives handlers operational continuation/resumption behavior and a selective CPS scheme. **[Inference]** Ordinary operation records cannot by themselves resume a suspended computation, implement multi-shot continuation choice or remove an effect soundly. BEAML should not advertise those later semantics based on dictionary syntax alone. Exceptions, retries, cancellation and process exits need explicit rules in either approach.

## Probes and open decisions

**[Proposal]** Test interval examples, arithmetic edge semantics, injected timeout/unknown, checked-conversion failure, fake foreign witness, callbacks with latent effects, closure creation versus invocation, discarded effectful results and manifest changes. Compare solver counterexamples by executing only safe deterministic reference cases. **[Unknown]** Predicate grammar/theory, timeout budget, effect polymorphism, handler scope/removal, foreign exception/process-exit mapping and recursion termination assumptions remain design choices. Type/effect safety does not establish secret-flow policy; see [information flow](../information-flow-security.md).
