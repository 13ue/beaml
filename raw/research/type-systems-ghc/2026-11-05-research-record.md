# Type systems and GHC - selected evidence record

Accessed 2026-11-05. Coverage is selected sections/source definitions and researcher paraphrases, not complete upstream documentation or papers. Examples in derived pages are original explanatory schematics, unexecuted and non-normative for BEAML. Copyright remains with original authors/publishers. No large source copies or paper PDFs are retained; no upstream license is assigned to BEAML.

## Version boundary

GHC User Guide evidence is explicitly 9.12.2 at downloads.haskell.org. Source observations use official ghc/ghc mirror tag `ghc-9.12.2-release`; tag immutability is not independently cryptographically verified and a commit SHA was not resolved. Current 9.15 search hits are deliberately not used as 9.12.2 evidence. Official GitLab wiki was blocked by Anubis and several individual source URLs failed retrieval; those failures do not establish their contents. The verified source files below suffice for selected pipeline trace but not every implementation subroutine. No GHC build/run or BEAML implementation occurred.

## Foundations

| ID | Author/publisher and exact source | Coverage and selected observation |
|---|---|---|
| F1 | Software Foundations, Programming Language Foundations, [Types](https://softwarefoundations.cis.upenn.edu/plf-current/Types.html), mutable current chapter | Typing and small-step progress/preservation. Closed well-typed terms do not become stuck within that defined calculus; not a theorem about foreign failures or termination. |
| F2 | Same authors, [Sub](https://softwarefoundations.cis.upenn.edu/plf-current/Sub.html) | Record/arrow subtyping and subsumption. Safe substitutability determines width/depth and function direction; independent from nominal equality. |
| F3 | Same authors, [References](https://softwarefoundations.cis.upenn.edu/plf-current/References.html) | Mutable stores extend typing/soundness obligations; ordinary expression typing alone is insufficient for state. |
| F4 | Robin Milner, [A Theory of Type Polymorphism in Programming](https://www.pure.ed.ac.uk/ws/files/15143545/1_s2.0_0022000078900144_main.pdf), JCSS17(1978)348-375, DOI10.1016/0022-0000(78)90014-4 | Selected algorithm W/soundness sections. Substitution-based inference for the specified ML-like core, distinct from arbitrary overloading/subtyping. Edinburgh publisher PDF includes a repository cover page; no copy redistributed. |
| F5 | Vytiniotis/Peyton Jones/Schrijvers/Sulzmann, [OutsideIn(X)](https://www.microsoft.com/en-us/research/publication/outsideinx-modular-type-inference-with-local-assumptions/), JFP21(2011)333-412 | Abstract and guide-linked local-generalization rationale; local equalities complicate principal inference; solver obligations matter. No full proof audit. |
| F6 | Peyton Jones/Vytiniotis/Weirich/Shields, [Practical type inference for arbitrary-rank types](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/putting.pdf), draft2007-07-31 | Abstract/selected bidirectional discussion: annotations enable practical checking beyond easy HM inference; no claim that all richer inference is automatic. |
| F7 | Philip Wadler's [type-class research page](https://homepages.inf.ed.ac.uk/wadler/topics/type-classes.html), Wadler/Blott POPL1989 and Hall/Hammond/Peyton Jones/Wadler ESOP1994 entries | Qualified source typing and dictionary-style elaboration, coherence research references. Author-hosted abstracts, not full original proof review. |
| F8 | Rondon/Kawaguchi/Jhala, [Liquid Types](https://goto.ucsd.edu/~rjhala/papers/liquid_types.html), PLDI2008 | Author-hosted abstract: HM inference +predicate abstraction/qualifiers. Does not mean arbitrary source predicates become decidable. |
| F9 | Jhala/Seidel/Vazou, [Refinement tutorial: simple refinements](https://ucsd-progsys.github.io/lh-workshop/02-refinements.html) | Refinement implication reduced to logical validity; logical predicate fragment constrained for SMT. |
| F10 | Barrett/Fontaine/Tinelli, [SMT-LIB2.7](https://smt-lib.org/papers/smt-lib-reference-v2.7-r2025-07-07.pdf), release2025-07-07 §§3.11,4.2 | check-sat returns sat/unsat/unknown; reason-unknown query. Solver outcomes must not be collapsed into success. No solver selected. |
| F11 | Daan Leijen, [Koka: Programming with Row-polymorphic Effect Types](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/paper-20.pdf),2014 | Abstract/intro: inferred type/effect rows and semantic effect claims under its calculus. |
| F12 | Leijen, [Algebraic Effects for Functional Programming](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/08/algeff-tr-2016-v3.pdf), MSR-TR-2016-29 updatedDec2016 | Abstract/selected compilation overview: operational handlers and selective CPS go beyond labeling calls. |
| F13 | Strom/Yemini, [Typestate](https://research.ibm.com/publications/typestate-a-programming-language-concept-for-enhancing-software-reliability), TSE1986; DOI10.1109/TSE.1986.6312929 | Author-affiliated IBM abstract: legal operations depend on state; aliasing/protocol control is not established by a marker alone. |

## GHC9.12.2 User Guide

Base: https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/

| ID / relative page | Inspected mechanism |
|---|---|
| G1 `exts/let_generalisation.html` §6.12.2 | MonoLocalBinds/closed free-variable conditions; richer local equalities restrict naive generalization. |
| G2 `exts/instances.html` §6.8.8 | Instance head matching, contexts not used to select matches, overlap and termination conditions. |
| G3 `exts/type_families.html` §6.4.9 | Associated/open/closed type computation, compatibility/termination issues. |
| G4 `exts/gadt.html` §6.4.8 | Matching GADT constructor refines local types, annotations needed; beyond ordinary ADTs. |
| G5 `exts/poly_kinds.html` §6.4.13 | Kinds classify constructors; polymorphic kinds and Haskell partial-correctness scope. |
| G6 `exts/roles.html` §6.4.24 | Nominal/representational/phantom roles control safe representation coercion, not ordinary subtype variance. |
| G7 `exts/linear_types.html` §6.4.21 | Multiplicity1/Many, exactly-once consumption condition, explicit arrows and experimental status. |
| G8 `using-warnings.html` §5.2, incomplete patterns and fmax-pmcheck-models | Symbolic uncovered models, potential exponential growth and precision cap; warnings may not be fatal. |
| G9 `debugging.html` §5.13 | Dump/check boundaries for parser/renamer/typechecker/Core/STG/Cmm/backend, Core lint; flags are inspection interfaces, not evidence checks were run. |
| G10 `runtime_control.html` §5.7 | RTS garbage collection/storage options; own runtime configuration, not BEAM semantics. |

## GHC source tag ghc-9.12.2-release

Source base: https://github.com/ghc/ghc/blob/ghc-9.12.2-release/

| ID / file | Inspected symbols/notes and observation |
|---|---|
| C1 `compiler/GHC/Driver/Main.hs` | hscTypecheckRename, myCoreToStg, doCodeGen; orchestrates frontend, Core-to-STG, StgToCmm and backend output. |
| C2 `compiler/GHC/Core.hs` | Expr, Case invariants; source→renamed names→typed identifiers→System FC explanation. Core has explicit Type/Coercion/Cast forms. |
| C3 `compiler/GHC/HsToCore.hs` | deSugar; typed syntax/evidence becomes ModGuts/Core. |
| C4 `compiler/GHC/Core/Opt/Pipeline.hs` | core2core/getCoreToDo; options configure simplify/specialize/demand/worker-wrapper/CSE and other passes. |
| C5 `compiler/GHC/Core/Lint.hs` | Note[Core Lint guarantee], Note[GHC Formalism]. Conditional guarantee excludes unsafe/invalid plugin coercions, requires complete cases and downstream correctness; checker does not prove arbitrary semantic equivalence. |
| C6 `compiler/GHC/CoreToStg.hs` | coreToStg, Note[Live vs free], Note[What are these SRTs all about?], nonescaping lets; operational closure/liveness boundary. |
| C7 `compiler/GHC/Stg/Syntax.hs` | StgArg, GenStgRhs, UpdateFlag; restricted pre-Cmm graph/closure representation. |
| C8 `rts/Updates.cmm` | stg_upd_frame/stg_marked_upd_frame; thunk update through indirection/blackhole and waiting-thread handling. |

Historical mechanism references: Vytiniotis/Peyton Jones [Practical aspects of evidence-based compilation in System FC](https://simon.peytonjones.org/system-fc/), draft2011-03; author warns it was superseded by two papers, so it is conceptual evidence not current9.12.2 formal spec. Peyton Jones [STG paper](https://www.microsoft.com/en-us/research/publication/implementing-lazy-functional-languages-on-stock-hardware-the-spineless-tagless-g-machine/), JFP1992 abstract; not identical to modern GHC STG. Neither paper was fully proof-audited.
