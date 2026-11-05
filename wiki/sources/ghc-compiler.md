---
id: source-ghc-compiler
kind: source-note
status: selected-pinned-source-research
updated: 2026-11-05
---

# GHC compiler: versioned source trace

**[Verified]** Evidence uses the GHC 9.12.2 User Guide and source tag `ghc-9.12.2-release` in the official [ghc/ghc mirror](https://github.com/ghc/ghc). Accessed 2026-11-05. The official mirror release page resolves the tag to commit `383be28ffdddf65b57b7b111bfc89808b4229ebc`; [ref-resolution evidence](../../raw/research/type-systems-ghc/2026-11-05-ghc-ref-resolution.json) supplements the immutable initial capture. No build or local signature verification was performed. The [raw research record](../../raw/research/type-systems-ghc/2026-11-05-research-record.md) and [capture provenance](../../raw/research/type-systems-ghc/2026-11-05-provenance.json) separate source inspection, blocked URLs and historical papers. Source copyright remains upstream; selected researcher notes only retained.

| Boundary | Inspected source / symbol | What to look for |
|---|---|---|
| Frontend | [Driver/Main.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Driver/Main.hs#L594), `hscTypecheckRename`, `hscParse`, `hscDesugar` | Phase entry points/diagnostics; parsed and renamed/typed trees differ. |
| Constraint/evidence finalization | [Tc/Module.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Module.hs#L488), `tcRnImports`/`tcRnSrcDecls` | Import consistency, simplifyTop evidence, fail-before-zonk ordering; [later capture](../../raw/research/type-systems-ghc/2026-11-05-ghc-typechecker-followup.md). |
| Typed Core | [Core.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core.hs#L121), explanation and `Expr` | System FC terms have explicit types, coercions and casts, not unresolved source overloading. |
| Desugaring | [HsToCore.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/HsToCore.hs#L103), `deSugar` | Typed module/evidence inputs ->Core `ModGuts`. |
| Middle end | [Core/Opt/Pipeline.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/Pipeline.hs#L69), `core2core`, `getCoreToDo` | Flag-dependent pipeline; simplify/specialize/demand/worker-wrapper and other passes. |
| IR validity | [Core/Lint.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Lint.hs#L105), Note[Core Lint guarantee] | Explicit preconditions and downstream assumptions; incomplete matches not checked by Core Lint. |
| Closure lowering | [CoreToStg.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/CoreToStg.hs#L53), `coreToStg`, live/free/SRT notes; [Stg/Syntax.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Stg/Syntax.hs#L123), `StgArg`, `GenStgRhs`, `UpdateFlag` | Restricted application/closure representation, operational liveness and retained CAF references. |
| Native backend seam | [Driver/Main.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Driver/Main.hs#L2098), `doCodeGen`, `myCoreToStg` | STG ->Cmm stream ->backend output orchestration; not a source-level safety theorem. |
| Lazy-runtime updates | [rts/Updates.cmm](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/rts/Updates.cmm#L32), update frames/blackholes | Update indirection and waiting-thread handling are runtime semantics, not merely syntax transformations. |

The [9.12.2 dump/check guide](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/debugging.html) exposes phase observations; the [roles guide](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/roles.html) explains coercion restrictions. Historical [System FC evidence paper](https://simon.peytonjones.org/system-fc/) (2011 draft, explicitly superseded) and [STG paper](https://www.microsoft.com/en-us/research/publication/implementing-lazy-functional-languages-on-stock-hardware-the-spineless-tagless-g-machine/) (1992) explain ideas, not current API contracts.

## Bounded solver and demand followup

**[Verified]** A later account-scoped connector read closed the earlier central-file access gap. [New selected supplement](../../raw/research/type-systems-ghc/2026-11-05-solver-demand-followup.md) and [file/blob provenance](../../raw/research/type-systems-ghc/2026-11-05-solver-demand-followup.provenance.json) record seven pinned source files. The original failed-fetch notes remain historical.

- [Solver/Solve.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver/Solve.hs#L154), `solveSimples/solveCt`: work selection, canonical shape/evidence, inert facts and restart.
- [Solver.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver.hs#L2743), `solveWanteds/solveImplication`: bounded simple/nested iteration and scoped givens/evidence/status.
- [Equality.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver/Equality.hs#L1863) and [Dict.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Solver/Dict.hs#L900): controlled metavariable assignment/requeue and selected-instance evidence/subgoals.
- [DmdAnal.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/DmdAnal.hs#L291): body-to-RHS versus signature-to-call demand, recursive fixed-point fallback and boxity constraints.
- [WorkWrap.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/WorkWrap.hs#L812) and [WorkWrap/Utils.hs](https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Core/Opt/WorkWrap/Utils.hs#L839): justified worker/wrapper metadata and non-automatic strict-argument splitting.

The [expanded walkthrough](../concepts/compilers/ghc.md#the-actual-solver-work-inert-facts-and-scoped-evidence) includes implication-scope and demand/unused-field examples. This selected mechanism inspection is not all solver/type-family/strictness cases or a GHC execution.

## Following one overloaded call

**[Inference]** In a schematic `same x y = x == y`, source resolution identifies the intended equality method; checking infers a class obligation; elaboration passes the chosen operation record; simplification may expose a concrete method; closure lowering chooses runtime layout. A type-equality coercion is different evidence from a method dictionary. The [worked GHC walkthrough](../concepts/compilers/ghc.md) makes these distinctions explicit and shows where a BEAML Schema witness could fit without copying lazy evaluation, STG or GHC's native RTS.

**[Unknown]** Not every solver/backend routine was inspected. GitLab commentary was access-blocked; GHC was not installed/run, and phase dumps are proposed experiments. No claim of complete GHC implementation mastery follows from this selected trace.
