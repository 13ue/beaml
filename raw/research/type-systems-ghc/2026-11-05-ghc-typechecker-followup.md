# GHC typechecker source followup

Accessed2026-11-05. Official ghc/ghc mirror commit383be28ffdddf65b57b7b111bfc89808b4229ebc; selected source inspection, no source bodies redistributed.

Source: https://github.com/ghc/ghc/blob/383be28ffdddf65b57b7b111bfc89808b4229ebc/compiler/GHC/Tc/Module.hs

Inspected `tcRnModule`, `tcRnImports`, `tcRnSrcDecls` around lines183-521. Import processing builds instance/family environments, loads relevant orphan interfaces and checks family consistency. Source declarations accumulate constraints; `simplifyTop` produces new evidence bindings; errors stop further successful compilation; final zonking follows simplification because unification may still occur there. This provides a concrete phase-order invariant beyond a generic “typecheck then desugar” diagram.

Other targeted fetches for Tc/Solver, Tc/Types/Evidence and Core/Opt/DmdAnal remained inaccessible in this environment. Their exact internals are not inferred from import names. Copyright retained by GHC authors; this is a selected paraphrase.
