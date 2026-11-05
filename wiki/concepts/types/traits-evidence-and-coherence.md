---
id: concept-traits-evidence-coherence
kind: mechanism-guide
status: researched-and-proposed
updated: 2026-11-05
---

# Trait evidence, coherence and associated types

**[Requirement]** BEAML wants coherent global instance resolution, no overlapping impls in v1, associated types phase 2, and Schema witnesses for generic outputs. Package orphan/coherence rules are open. [Spec S03/S05/S20](../../sources/engineering-spec-v0.5.md). All code is explanatory pseudocode, unexecuted and non-normative.

## Elaborate an implicit obligation into an explicit value

**[Verified]** [Wadler's author-hosted type-class papers](https://homepages.inf.ed.ac.uk/wadler/topics/type-classes.html) describe translating overloading into explicitly typed programs. **[Proposal]** Consider this dictionary-shaped candidate lowering:

```text
trait Render<T> { render: T -> String }
fn describe<T:Render>(x:T) -> String = render(x)

-- elaborated form (schematic)
record RenderDict<T> { render: T -> String }
describe<T>(d:RenderDict<T>, x:T) = d.render(x)
```

An impl for Invoice supplies `invoice_render_dict`. A caller `describe(invoice)` solves Render<Invoice> then inserts that dictionary. An impl for List<T> may itself need Render<T>, so resolution builds `list_dict(element_dict)`. The evidence graph must terminate; repeatedly requesting a dictionary through the same unresolved type goal must not recurse forever. The dictionary contains executable behavior, unlike an erased type parameter. It can be passed through a generated BEAM ABI as a closed operation record or module/function capability; either needs concrete representation and trust rules.

**[Proposal]** Typechecking a trait method and choosing its implementation are different passes. `render:Invoice->String` may typecheck for two implementations that produce different text. Both are locally valid; global coherence requires the same source constraint have an unambiguous intended meaning across packages/build order. A first v1 can reject intersecting impl heads at declaration import time and require explicit evidence for ambiguous user-selected policies, rather than silently choosing “first loaded.” Exact orphan ownership/closed-world linking rules remain decisions.

## Why instance contexts cannot simply resolve overlap

**[Verified]** [GHC 9.12.2 instance resolution](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/instances.html) matches instance heads without using contexts to choose candidates, and documents overlap/termination rules. **[Proposal]** Suppose two impl heads both match `Codec<List<Int>>`, one requiring Ordered<Int> and another Sensitive<Int>. Picking whichever context currently happens to resolve makes behavior change when a dependency adds a new impl. Reject the overlap under BEAML's v1 rule instead; context satisfiability is not a stable priority scheme.

A useful resolution trace records normalized goal, candidate heads, substitution, rejected-overlap reason, nested obligations, selected impl identity and dependency/interface fingerprint. This trace can explain trait errors, drive “go to implementation,” and invalidate callers when imported impls change. A query that tracks only the function body but not its impl environment can cache the wrong dictionary even though its type is unchanged.

## Associated types add equality evidence

**[Proposal]** A future `trait Source { type Item; next:Self->Option<Item> }` makes `Item<Invoices>` normalize via the selected impl. Calling next then checking Invoice fields needs that equality, not just a method pointer. Reject two conflicting Item equations even if both next bodies typecheck. Recursive family equations require termination/fuel/UNKNOWN diagnostics; injectivity cannot be assumed (`Item<A>=Item<B>` does not imply A=B).

**[Verified]** [GHC type families9.12.2](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/type_families.html) distinguishes open/closed and associated computation. [System FC](../../sources/ghc-compiler.md) makes type-equality evidence explicit. **[Inference]** BEAML need not implement System FC wholesale to preserve the distinction: method evidence, equality evidence and runtime schema evidence have different jobs.

**[Verified]** [GHC's actual dictionary solver](../compilers/ghc.md#the-actual-solver-work-inert-facts-and-scoped-evidence) first tries inert evidence/instances on rewritten goals, then constructs selected evidence from new nested obligations. **[Proposal]** A BEAML resolution record should therefore identify the evidence constructor and prerequisites as well as the selected implementation; “goal solved” alone cannot generate a generic runtime Schema/Validate call. Keep failed/ambiguous/bounded searches distinct from successful evidence.

## Roles are not subtype variance

**[Verified]** [GHC roles9.12.2](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/roles.html) controls representation coercions through nominal/representational/phantom positions, including type-family interactions. **[Proposal]** A BEAML `Validated<T>` or `Stream<State,T>` must not permit an otherwise zero-cost representation cast to forge T or State. A state parameter unused in fields can still require a nominal boundary for correctness. Merely marking it phantom in a compiler representation is not permission to expose arbitrary relabeling.

## Validation probes

**[Proposal]** Build a corpus of unique direct impls, nested generic obligations, conflicting impls imported through two dependency paths, cyclic goals, unrelated new impls, and associated output equations. Verify deterministic dictionary selection independent of file/package iteration; resolution trace spans point to conflicting declarations. Run an imported-impl edit through fresh/incremental compilation and compare generated call targets. For Schema/Validate deriving, ensure generated evidence recursively refers to the exact type/schema version and cannot bypass refinement hooks. No trait engine or dictionary ABI has been implemented. [Witness mechanisms](typestate-and-schema-witnesses.md).
