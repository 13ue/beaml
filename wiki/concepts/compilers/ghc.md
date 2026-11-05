---
id: concept-compiler-ghc
kind: compiler-walkthrough
status: selected-source-trace-and-proposals
updated: 2026-11-05
---

# GHC: evidence-preserving compilation and lazy-runtime lowering

**[Verified]** This walkthrough follows selected GHC 9.12.2 source at tag `ghc-9.12.2-release`, with historical papers labeled separately. Exact files/notes are in the [GHC source ledger](../../sources/ghc-compiler.md). It traces mechanisms, not every branch of a production compiler. The examples and suggested dump experiment are unexecuted. **[Requirement]** BEAML targets generated BEAM source, so GHC is a reference for typed lowering/evidence/invariants, not its selected backend or evaluation model. [Spec S07/S09](../../sources/engineering-spec-v0.5.md).

## Frontend: names before meanings, constraints before evidence

**[Verified]** [GHC.Core's pipeline explanation](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core.hs#L121) distinguishes parsed reader names, renamed unique names and typed identifiers. [Driver.Main](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Driver/Main.hs#L594) exposes parse/typecheck-rename/desugar entry points. **[Inference]** A source identifier spelled x in two scopes is not one symbol; attaching type facts to text alone breaks shadowing/rename.

Original Haskell-like schematic:

```haskell
same x y = x == y
answer = same (3 :: Int) 3
```

**[Proposal, explanatory model]** Parse preserves application/binding structure and locations. Resolve `==` to the imported equality method and x/y to local binding identities. Assign fresh typeα to x/y, generate both equality/application constraints and the class goal Eqα. A checking signature supplies assumptions; inference supplies metavariables. Solver substitution replaces solved metavariables; remaining quantified variables/constraints become the function's type and evidence parameters. If `same (3 :: Int) True` is attempted, matching x/y types conflicts; no method dictionary fixes Int=Bool. [Inference foundations](../types/type-inference-and-polymorphism.md), [trait evidence](../types/traits-evidence-and-coherence.md).

The exact production solver handles more than this model. [OutsideIn(X)](https://www.microsoft.com/en-us/research/publication/outsideinx-modular-type-inference-with-local-assumptions/) motivates local assumptions/constraint solving, while GHC's [local generalization rules](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/let_generalisation.html) show why blindly applying HM generalization is insufficient.

**[Verified]** The pinned [GHC.Tc.Module source](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Module.hs#L488) makes the ordering concrete: declaration checking collects constraints; `simplifyTop` produces evidence; errors abort; `zonkTcGblEnv` follows because solving may still unify variables. Its import phase loads relevant orphan interfaces and checks type-family consistency. **[Inference]** Imported evidence environments are semantic inputs, and freezing types before final constraint solving would be premature. [Followup capture](../../../raw/research/type-systems-ghc/2026-11-05-ghc-typechecker-followup.md).

## The actual solver: work, inert facts and scoped evidence

**[Verified]** At the pinned commit, [Solver/Solve.hs:solveSimples/solveCt](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver/Solve.hs#L154) emits/selects work items, rewrites/classifies constraints and dispatches equalities, dictionaries or quantified predicates. A constraint is discharged, restarted after rewriting, or retained inert for later interaction. Canonicalization is a shape/evidence operation, not a one-time global “normalization done” flag. [Equality.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver/Equality.hs#L1863) permits unification only under role/flavor/touchability/shape conditions; success fills equality evidence and requeues affected constraints. [Selected source capture](../../../raw/research/type-systems-ghc/2026-11-05-solver-demand-followup.md).

**[Proposal, explanatory trace]** With wanted goals `α ~ Int` and `Eq α`, solving the first can assign a touchable α, produce reflexive equality evidence, and make `Eq Int` available for dictionary resolution. If Eqα was previously inert, the new equality invalidates its old simplified form. [Dict.hs:chooseInstance](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver/Dict.hs#L900) constructs selected-instance evidence from fresh nested wanted evidence, rather than returning just a boolean. For Eq<List<Int>>, the conceptual dictionary constructor consumes Eq<Int> evidence. The exact selected instances/defaulting rules are version-specific; this is not an executed solver dump.

**[Verified]** [Solver.hs:solveWanteds/solveImplication](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver.hs#L2743) iterates simple/nested goals with unification feedback and bounds, and solves each implication in a nested evidence/level scope with its givens before restoring outer state. Residual obligations receive solved/unsolved/insoluble status. [Wanted-forall elaboration](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver/Solve.hs#L396) creates skolems/given evidence and builds an evidence function around a nested implication.

**[Proposal, explanatory counterexample]** In a branch that learns given `a ~ Int`, a wanted Eq<a> can use that local equality. The sibling branch/outside context must not inherit `a=Int` as a global substitution. Likewise, checking `forall a. a -> a` must not solve rigid a by choosing Int for a body returning 3. Distinguish local givens, solvable metavariables, wanted evidence and implication scope. For BEAML traits/refinements/effects this argues for explicit assumptions, bounded work/cycle policy and scoped error evidence; importing GHC's entire solver or its inference compromises remains unnecessary.

## Desugaring: make hidden choices explicit

**[Verified]** [HsToCore.deSugar](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/HsToCore.hs#L103) takes typed module state including evidence bindings and returns Core module guts. Core's `Expr` includes lambda/application/let/case, Type, Coercion and representational Cast forms. This is typed System FC rather than a source AST with unresolved overloaded operators.

**[Proposal, explanatory model]** Lower same conceptually to `Λa. λ(eqDict:Eq a). λx:a. λy:a. eqMethod eqDict x y`; answer supplies Int and its Eq dictionary. The dictionary has executable methods; a System FC coercion instead witnesses a type equality, allowing a justified cast. A GADT branch may learn `a ~ Int`; a type-family reduction may require a different equality proof. They must not be replaced by a user-controlled runtime boolean. Historical [FC evidence research](https://simon.peytonjones.org/system-fc/) explains explicit erasable equality witnesses and lazy-evaluation hazards; its 2011 draft is superseded, not the 9.12.2 formal definition.

**[Inference]** BEAML's Schema/Validate/effect dictionaries can likewise become explicit MIR operands/capabilities. Refinement obligations and privacy releases need distinct evidence kinds; erasing a check before its result is established would forge trust. Keep authored source origins on desugared operations so a generated dictionary/validator failure is explainable.

## Core optimization: local rewriting under global invariants

**[Verified]** [Core.Opt.Pipeline](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/Pipeline.hs#L69) assembles flag-dependent passes including simplification, specialization, demand analysis, worker-wrapper and CSE. **[Proposal, explanatory model]** If same's concrete dictionary is known, inlining/specialization may reveal Int equality and avoid generic field selection. A worker can operate on a lower-level representation while a wrapper preserves the public calling convention. These transformations require type/scope/representation and evaluation-order invariants, not merely text substitution.

Capture avoidance illustrates a failure: inline `λx.y` into a context binding y without freshening, and a free y can become the wrong local variable. Duplicating an expression with a network effect can duplicate requests even if both results have the same type. Floating a failing/cancelable operation outside a branch can change observable behavior. **[Proposal]** BEAML needs a defined effect/error/cancellation semantics before borrowing rewrites; GHC optimizations tuned for pure lazy expressions do not authorize moving external operations.

**[Verified]** [Core Lint, Note[Core Lint guarantee]](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Lint.hs#L105) states assumptions including no unsafe coercions, valid plugin evidence, complete case matches and correct downstream compilation. It explicitly does not check incomplete cases. **[Inference]** A verifier decouples some safety checks from a complex inference engine but cannot substitute for source/IR semantic differential tests, privacy-label preservation or backend correctness.

## Demand analysis earns a worker's calling convention

**[Verified]** [DmdAnal.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/DmdAnal.hs#L291) propagates demand through expressions and annotates binders. LetUp analyzes a local binding's body first, then its RHS under the resulting use demand; LetDown computes function signatures used by calls, with a bounded recursive fixed point. If that iteration fails, the implementation performs a conservative extra traversal and clears strong signatures rather than returning stale optimistic annotations. [Boxity invariant](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/DmdAnal.hs#L168) forbids changing unboxing promises when no worker/wrapper pass will realize them.

**[Proposal, explanatory trace]** For a lazy pair argument where a function returns only the first Int field plus 1, demand distinguishes forcing the outer constructor, needing the first field's numeric value, and not using the second field. A valid optimization may pass a needed unboxed integer to an internal worker while the public wrapper matches the pair and preserves lazy behavior of the unused field. If the second field diverges, forcing it merely to “simplify the representation” changes semantics. Absence, strictness, usage/cardinality, boxity and constructed-result facts are related but distinct; a type alone does not authorize forcing.

**[Verified]** [WorkWrap.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/WorkWrap.hs#L812) consumes demand/CPR information, builds worker+wrapper bindings and updates arity/demand/unfolding metadata. [WorkWrap/Utils.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/WorkWrap/Utils.hs#L839) explicitly separates strict non-product arguments from automatic unboxing/splitting; optional CBV worker behavior has flag/code-size/RULE tradeoffs. Thus “strict argument” does not mean every pass may change its calling convention.

**[Proposal]** A BEAML optimizer should similarly connect analysis facts to transformations/ABI invariants and invalidate them when rewrites change usage. Its eager/effectful BEAM semantics need their own laws: no duplication or movement of LLM/network/validation/release operations merely because a value is used once or a type matches. Probe recursive-analysis fallback, unused/failing fields, demand facts surviving rewrites and wrapper/public ABI equivalence before adopting such an optimization. No demand-analysis or worker benchmark was run here.

## CorePrep/STG: from expressions to operational closures

**[Verified]** [Driver.Main.myCoreToStg](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Driver/Main.hs#L2177) invokes Core-to-STG and STG passes; [CoreToStg's live/free/SRT notes](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/CoreToStg.hs#L53) explain operational liveness, nonescaping bindings and CAF retention. [STG syntax](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Stg/Syntax.hs#L123) restricts call arguments and represents constructor/closure RHSs with update information. These are layout/control decisions beyond static types.

**[Proposal, explanatory model]** `let shared = expensive x in pair shared shared` may allocate one thunk capturing x. Demanding it evaluates once and updates the shared closure; an escaping lambda captures its free values, while a proven nonescaping tail-call join can use a jump-like implementation instead of a heap closure. Liveness matters because references held only in closure environments can keep data alive after the original variable's last lexical occurrence. A source-level type does not imply short lifetime or zeroized storage.

## Cmm and backends: preserve calling and GC contracts

**[Verified]** [Driver.Main.doCodeGen](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Driver/Main.hs#L2098) orchestrates STG-to-Cmm and streams groups through later generation, avoiding retaining all low-level output at once. The [debug guide](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/debugging.html) distinguishes Core, STG, Cmm and native/LLVM/backend dumps. **[Inference]** At this boundary closure layout, registers/stack, heap checks and live-root descriptions become runtime contracts. “Typed frontend” alone does not prove those machine interfaces correct.

**[Proposal]** BEAML's first backend stops earlier: emit one source dialect plus guards/metadata, let OTP handle its own lowering/GC/JIT, and validate that generated values/calls preserve BEAML semantics. Do not add a custom STG/Cmm/native runtime when the spec explicitly chooses BEAM. Compare with the independently researched [BEAM boundary](../beam-runtime-and-interop.md) and other compiler source traces when available.

## Laziness, strictness, blackholes and garbage collection

**[Verified]** The historical [STG paper 1992](https://www.microsoft.com/en-us/research/publication/implementing-lazy-functional-languages-on-stock-hardware-the-spineless-tagless-g-machine/) targets non-strict higher-order execution. Current [Updates.cmm](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/rts/Updates.cmm#L32) updates thunks via indirection and handles blackholed computations/waiting threads. RTS [GC options9.12.2](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/runtime_control.html) belong to GHC's runtime, not OTP.

**[Inference]** Laziness changes observable termination: `const 1 diverge` can produce 1 if the second argument is not demanded, whereas an eager call evaluating diverge first cannot. Strictness analysis must establish demand before changing evaluation; exceptions and infinite computations complicate equivalence. A blackhole represents a thunk being evaluated/sharing coordination, not a BEAM mailbox or generic deadlock proof. Garbage collection reclaims unreachable representation; it does not imply immediate reclamation, secrecy or cleanup of external resources.

**[Proposal]** BEAML should specify eager/lazy evaluation, field evaluation, sequencing and cancellation directly. Do not inherit bottom/nontermination, lazy IO-related reasoning, thunk sharing or native thread/GC behavior just because typeclass dictionaries and HIR/MIR look functional. [Foundations](../types/type-system-foundations.md) describes the necessary theorem scope.

## A reproducible inspection probe

**[Proposal]** In an isolated pinned GHC 9.12.2 environment, compile a tiny Eq-constrained function at O0/O2 with the guide's parsed/renamed/typechecked, desugared/simplified Core, STG and Cmm dumps plus Core Lint. Inspect whether evidence/type arguments disappear, which method specializes, where closure/update flags occur and which source metadata survives. Add an incomplete match and a GADT branch to see the different checker responsibilities. Retain commands/versions/normalized artifacts and compare behavior; do not golden incidental unique names.

**[Unknown]** This experiment was not run. The release tag was later resolved through the official mirror to `383be28ffdddf65b57b7b111bfc89808b4229ebc`; selected solver/demand files were successfully re-read through the account-scoped connector after earlier web failures; other GitLab commentary remains blocked. The knowledge here is a selected mechanism trace with explicit checks/assumptions, not an exhaustive audit of GHC or proof that BEAML can reuse its guarantees.
