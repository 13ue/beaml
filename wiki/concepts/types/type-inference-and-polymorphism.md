---
id: concept-type-inference-polymorphism
kind: mechanism-guide
status: researched-and-proposed
updated: 2026-11-05
---

# Type inference, generalization and kinds

**[Requirement]** BEAML specifies local expression inference and generics; associated types are phase 2, higher-kinded types/GADTs/type families later. It does not require unrestricted inference. [Spec S03-S05/S20](../../sources/engineering-spec-v0.5.md). Examples below are schematic/unexecuted, not normative BEAML syntax.

## A small unification trace

**[Verified]** Milner's [1978 algorithm W](https://www.pure.ed.ac.uk/ws/files/15143545/1_s2.0_0022000078900144_main.pdf) uses substitution/unification for its chosen polymorphic core. It does not directly settle effects, structural subtyping or arbitrary type-class search. **[Proposal]** Use the following minimal trace to define BEAML inference invariants before choosing an implementation:

```text
let identity = λx.x
let a = identity(7)
let b = identity(true)
```

1. Assign x fresh metavariableα. Its occurrence hasα, so the lambda has `α -> α`.
2. Generalize only variables not free in the surrounding environment: `identity : forall α. α -> α`.
3. At the first occurrence instantiate freshβ; application constrainsβ=Int, so result Int.
4. At the second instantiate freshγ; constrainγ=Bool. β andγ are unrelated, so both calls work.

If occurrence instantiation reuses the same metavariable, the first call fixes identity to Int and incorrectly rejects the second. Conversely, generalizing a variable captured from Γ can accept an invalid program. For `λouter. let captured = outer in (captured(7), captured(true))`, captured is the same unknown function supplied once; its type variables are free in Γ and cannot become independent polymorphic choices.

**[Proposal]** Unification must prune substitutions, reject mismatched constructors/arity, and perform occurs checks. The term `λx.x(x)` constrainsα=`α -> β`; permitting that recursive equation without an explicit recursive-type theory makes the solver loop or silently admit unintended infinite types. Check substitution composition/order and freshening under binders with generated small terms; keep user spans attached to constraints so diagnostics explain which use demanded Int versus Bool.

## Generalization interacts with effects and local equalities

**[Proposal]** A mutable reference holding `[]` must not be generalized as if each read/write had an independent element type. One use could store Int and another read Bool. Choose an effect-aware generalization rule or a restrictive syntactic/value rule before adding references/foreign mutable values. Similarly, recursively polymorphic functions may need signatures; do not assume a recursive call can instantiate a fresh arbitrary type while inferring its own definition.

**[Verified]** GHC 9.12.2 [MonoLocalBinds](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/let_generalisation.html) limits local generalization in the presence of features such as GADTs/type families, using top-level/closed-variable conditions. [OutsideIn(X)](https://www.microsoft.com/en-us/research/publication/outsideinx-modular-type-inference-with-local-assumptions/) explains inference with local assumptions. **[Inference]** This is a warning that adopting GADT syntax changes the inference contract, not a reason to copy every GHC restriction into BEAML.

## Synthesis and checking can have different jobs

**[Proposal]** A practical core can synthesize a type for ordinary expressions but check a lambda/body against an explicit exported signature. For checking `λx.x` against `T -> T`, bind x:T and verify its body:T; no guessing needed. For a polymorphic signature, replace universally quantified variables with rigid skolems while checking, preventing an implementation from pretending its arbitrary T is always Int. A body returning 7 cannot satisfy `forall T. T -> T` simply by unifying T with Int.

**[Verified]** The [arbitrary-rank inference paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/putting.pdf) uses practical annotation-directed checking beyond ordinary HM. **[Proposal]** Keep BEAML's first version rank 1 unless a requirement needs more: `forall T. T -> T` at an outer binding is simpler than accepting a parameter that itself must work at every T. Document inference failure as “signature required” when supported checking can succeed, rather than claiming the expression is semantically impossible.

## Kinds and deferred expressiveness

**[Verified]** GHC [kind polymorphism9.12.2](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/poly_kinds.html) classifies type constructors as well as ordinary types. **[Proposal]** In a simple BEAML kind checker, Int:Type, List:Type->Type, List<Int>:Type; writing List<List> fails because List expects a Type argument, not a constructor. A higher-kinded parameter `F:Type->Type` would permit generic `map<F>`; it requires constructor unification/kind checking and is explicitly deferred by the spec.

**[Verified]** [GADTs9.12.2](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/gadt.html) refine local type equalities on matches. In an illustrative `Expr<T>`, `IntLit:Int->Expr<Int>` lets its matching branch know T=Int; ordinary `Box<T>` does not. [Type families](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/type_families.html) compute at type level, so associated output normalization/termination become obligations. These are distinct from restricted natural-number const expressions; a const evaluator also needs range/overflow/normal-form rules.

## Constraint solving must preserve assumption scope

**[Verified]** The pinned GHC [solver walkthrough](../compilers/ghc.md#the-actual-solver-work-inert-facts-and-scoped-evidence) now traces actual worklist/inert processing and nested implication evidence. **[Inference]** Unification is not an unrestricted assignment to any type variable: skolems and local given equalities have different scope from touchable metavariables. A local `a~Int` assumption cannot escape a branch and silently specialize all callers. **[Proposal]** Include branch-local equality, skolem escape, requeued constraints after substitution, recursive-goal limits and residual-unsolved diagnostics in BEAML's inference corpus. These examples extend the local HM trace without importing all GHC extensions.

## BEAML design boundary and probes

**[Unknown]** Required signatures, numeric literal defaulting, record row inference versus subtyping, effect polymorphism, recursive generalization, package interface type schemes and const-evaluation bounds are not selected. **[Proposal]** Test identity freshening, captured-variable non-generalization, occurs-check failure, rigid signature checking, effectful-cell rejection, recursive signature requirements and kind/arity errors. Compare inferred types modulo bound-variable renaming, not incidental metavariable numbers. Save minimal counterexamples for stale substitution and incremental imported-signature changes. [Traits](traits-evidence-and-coherence.md) adds evidence search; [effects](refinements-and-effects.md) adds latent behavior constraints.
