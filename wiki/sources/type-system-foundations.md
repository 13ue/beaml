---
id: source-type-system-foundations
kind: source-note
status: selected-primary-research
updated: 2026-11-05
---

# Type-system foundations: evidence map

**[Verified]** This source note maps inspected primary teaching texts, author-hosted papers and a solver standard to mechanisms. [Raw selected notes](../../raw/research/type-systems-ghc/2026-11-05-research-record.md) and [provenance](../../raw/research/type-systems-ghc/2026-11-05-provenance.json) record source IDs/versions/coverage. Attributed paraphrases are retained; full papers are not redistributed. Accessed 2026-11-05. Paper abstracts/selected sections were inspected, not complete theorem audits.

| Question | Primary evidence / exact section | Mechanism supported |
|---|---|---|
| What does type safety mean? | Software Foundations [Types](https://softwarefoundations.cis.upenn.edu/plf-current/Types.html), Type Soundness; [Sub](https://softwarefoundations.cis.upenn.edu/plf-current/Sub.html), subtyping rules; [References](https://softwarefoundations.cis.upenn.edu/plf-current/References.html), store typing | Small-step preservation/progress are conditional on the defined language/state. Subsumption and stores introduce separate proof obligations. |
| How can local inference work? | Milner [1978 paper](https://www.pure.ed.ac.uk/ws/files/15143545/1_s2.0_0022000078900144_main.pdf), algorithm W; [OutsideIn(X)](https://www.microsoft.com/en-us/research/publication/outsideinx-modular-type-inference-with-local-assumptions/), JFP2011; [Practical arbitrary-rank inference](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/putting.pdf),2007 draft | Fresh metavariables, substitution/unification and constrained generalization for a chosen core; richer local assumptions require restricted inference/annotations. |
| How are traits implemented? | Wadler's [type-class research index](https://homepages.inf.ed.ac.uk/wadler/topics/type-classes.html), Wadler/Blott 1989 and Hall et al 1994; [GHC instance resolution9.12.2](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/instances.html) | Qualified typing elaborates selected operations into explicit evidence; uniqueness/termination are distinct from checking method signatures. |
| What can refinements establish? | Rondon/Kawaguchi/Jhala [Liquid Types](https://goto.ucsd.edu/~rjhala/papers/liquid_types.html), PLDI2008; Jhala et al [simple refinements](https://ucsd-progsys.github.io/lh-workshop/02-refinements.html); Barrett et al [SMT-LIB2.7](https://smt-lib.org/papers/smt-lib-reference-v2.7-r2025-07-07.pdf), §§3.11/4.2 | Predicate abstraction and implication validity for chosen theories; solver sat/unsat/unknown must remain distinct. |
| What is more than an effect annotation? | Leijen [Koka effect rows2014](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/paper-20.pdf); [handlers2016](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/08/algeff-tr-2016-v3.pdf) | Latent effects join at calls; polymorphism needs row variables/constraints; resumable handlers add operational continuation behavior. |
| Does a state parameter own a resource? | Strom/Yemini [Typestate](https://research.ibm.com/publications/typestate-a-programming-language-concept-for-enhancing-software-reliability),1986; [GHC linear types9.12.2](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/linear_types.html) | Protocol state limits legal operations; usage multiplicity is an additional discipline, not implied by a phantom marker. |

## A worked evidence distinction

**[Inference]** Suppose a program checks `amount >= 0` at a model boundary. Successful decoding establishes the structural amount type; a checked predicate establishes the selected refinement for that value; a type-safe call prevents mismatched arguments; an effect check restricts operations. None of these establishes that an invoice was approved by the right person or that an LLM's amount is true. Those require separate policy/domain/evidence. [Spec p.2 §3 and pp.4-5 §§7-9](engineering-spec-v0.5.md).

**[Proposal]** The concepts turn this distinction into mechanisms and failure examples: [foundations](../concepts/types/type-system-foundations.md), [inference](../concepts/types/type-inference-and-polymorphism.md), [trait evidence](../concepts/types/traits-evidence-and-coherence.md), [refinements/effects](../concepts/types/refinements-and-effects.md), [typestate/witnesses](../concepts/types/typestate-and-schema-witnesses.md). Each proposes validation probes; no snippet has been executed or accepted as normative BEAML grammar.
