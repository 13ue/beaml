# GHC solver and demand-analysis followup

Accessed2026-11-05. Official ghc/ghc GitHub mirror commit383be28ffdddf65b57b7b111bfc89808b4229ebc (GHC9.12.2). Account-scoped GitHub connector confirmed the Solver directory and returned files; selected definitions/notes below read. Earlier web fetch failures are superseded for these paths, not for all possible GHC internals. Retained researcher paraphrases only; upstream copyright remains GHC authors'. Files were not built/run or copied here in full.

Source base: https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/

| File / sections inspected | Selected observation |
|---|---|
| compiler/GHC/Tc/Solver/Solve.hs lines54-287,396-460 | Actual solveSimples emits/selects work items; solveCt handles rewritten equality/dictionary/quantified shapes with Stop/StartAgain and inert retention. Header stage-plan prose is an overview; actual branching code is the inspected authority. Wanted forall elaborates skolem/given parameters and an implication into evidence function. |
| compiler/GHC/Tc/Solver.hs lines2743-2815,2927-3050 | solveWanteds iterates simple/nested implication solving, reacts to unification and bounds iterations. solveImplication nests evidence/level/givens, solves residual wanteds, restores scope and assigns solved/unsolved/insoluble status. |
| compiler/GHC/Tc/Solver/Dict.hs lines72-108,890-941 | Rewritten dictionaries try inert evidence then instances; selected instance creates nested wanted goals and fills evidence binding via instance constructor. |
| compiler/GHC/Tc/Solver/Equality.hs lines103-128,1863-1935 | Equality canonicalization/rewrite/inert reactions; unification needs wanted nominal equality, touchable meta-variable and shape checks. Successful assignment creates reflexive evidence and kicks affected constraints out for reprocessing. Given equalities are not blindly unified. |
| compiler/GHC/Core/Opt/DmdAnal.hs lines93-146,168-200,291-400,464-595,2263-2340 | Demand annotations flow through calls/lambdas/cases; LetUp analyzes body then RHS under use demand, LetDown makes function signatures and recursive groups use bounded fixpoint. Aborting fixpoint performs a conservative extra pass/zap rather than retaining stale strong annotations. Boxity must not change unless worker/wrapper follows. |
| compiler/GHC/Core/Opt/WorkWrap.hs lines41-72,790-880 | Uses strictness/CPR facts to build worker+wrapper and update IdInfo; worker arity/demand/unfolding identity must agree. |
| compiler/GHC/Core/Opt/WorkWrap/Utils.hs lines839-885 | Strict non-product arguments do not automatically split; optional CBV worker route has code-size/RULE tradeoffs and flag control. Strictness is not synonymous with unconditional unboxing. |

Coverage is selected central solver/demand mechanisms, not all equality/instance/family/strictness cases or a theorem audit. Maintained GHC/inference/trait pages explain original unexecuted examples and BEAML implications. No numerical performance or correctness result was reproduced.
