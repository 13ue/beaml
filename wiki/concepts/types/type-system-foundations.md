---
id: concept-types-foundations
kind: mechanism-guide
status: researched-and-proposed
updated: 2026-11-05
---

# Type-system foundations and the scope of safety

**[Requirement]** BEAML wants primitives, nominal newtypes, structural records, tagged ADTs, generics, exhaustive matches and safe-core type soundness, subject to explicit foreign/runtime effects. It has not fixed record subtyping or variance. [Spec S03/S09/S20, physical pp.2-3,7](../../sources/engineering-spec-v0.5.md). This page develops a candidate small-core reasoning method; all examples are unexecuted, non-normative schematics.

## Read a judgment as a claim with assumptions

**[Verified]** Small-step safety separates typing from evaluation: progress excludes stuck closed typed terms; preservation keeps their type across steps. Software Foundations [Types, Type Soundness](https://softwarefoundations.cis.upenn.edu/plf-current/Types.html) supplies a complete small example. That theorem does not establish termination, authorization or truth.

**[Proposal]** Give BEAML a judgment such as `Γ ⊢ e : T ! E`, where Γ maps names to types/assumptions and E describes allowed effects. Define evaluation `〈e,σ〉 → 〈e',σ'〉` once mutable/runtime stateσ exists. Before proving anything, define values, terminal errors/cancellation, effect transitions and “stuck.” A network timeout can be a specified `Err(Timeout)` outcome rather than a type failure. A process disappearing without the promised result needs its own operational rule. Store typing is a separate obligation; [Software Foundations References](https://softwarefoundations.cis.upenn.edu/plf-current/References.html) illustrates why adding state changes the theorem.

Schematic rule: if `Γ⊢c:Bool`, `Γ⊢a:T`, `Γ⊢b:T`, then `Γ⊢if c then a else b:T`, joining branch effects. With `c=true`, the evaluator chooses `a`, which retains T. Accepting `if 3 then a else b` breaks progress; typing branches as Int and String but claiming Int breaks preservation unless a specified common supertype/union and runtime representation are inserted.

**[Proposal]** State three claims separately: checker soundness (accepted source has a derivation), core safety (typed evaluation avoids defined type-stuckness), and compiler preservation (lowered behavior matches source). A correct typechecker cannot repair backend misordered effects or a foreign decoder returning an invalid nominal ID. A MIR verifier catches some malformed IR; it does not prove source-to-MIR semantic equivalence. See [GHC's conditional Core Lint guarantee](../../sources/ghc-compiler.md).

## Nominal identity, structural compatibility and representation differ

**[Proposal]** Treat the following as separate questions:

```text
newtype InvoiceId = UUID
newtype CustomerId = UUID
record Named = {name: String}
record Contact = {name: String, email: String}
```

Equal runtime representation does not make InvoiceId=CustomerId. An explicit constructor/decoder may establish each identity, and scoped access to that constructor matters. Structural width subtyping could allow Contact where Named is read-only expected; this does not mean the two schema identities or generated ABI descriptors are interchangeable. [Software Foundations Sub, record and arrow rules](https://softwarefoundations.cis.upenn.edu/plf-current/Sub.html) grounds substitutability; [GHC roles](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/exts/roles.html) grounds the distinct representation-coercion question.

For function substitutability, a consumer needing `Named -> Bool` cannot receive a function that accepts only Contact, because it may supply a record without email. A function accepting Named can serve a Contact caller. Parameters therefore reverse the subtype direction; results preserve it. Writable cells/foreign mutable collections need stricter treatment: if a Contact cell could be viewed as a writable Named cell, writing `{name:"Ada"}` would leave the original reader without email. A candidate BEAML v1 should either exclude mutable structural subtyping or make such type parameters invariant. That is a design proposal, not an adopted variance rule.

## ADTs and exhaustiveness are executable distinctions

**[Proposal]** For `Status = Draft | Approved | Paid`, coverage starts with the constructor set. Checking arms Draft then Approved subtracts those alternatives and leaves Paid as a concrete missing witness. Guards require more than constructor subtraction: `Approved if amount>0` still leaves an Approved value when the guard is false. Nested products generate combinations; cap analysis conservatively rather than convert timeout into exhaustive success.

**[Verified]** GHC 9.12.2's [pattern-warning documentation](https://downloads.haskell.org/ghc/9.12.2/docs/users_guide/using-warnings.html#ghc-flag--fmax-pmcheck-models%3D%E2%9F%A8n%E2%9F%A9) describes symbolic model splitting and a cap that forgets refinements to control growth. GHC warnings are configurable; BEAML's required exhaustive matching must choose its own blocking policy. A GADT match additionally learns a type equality; that is [deferred complexity](type-inference-and-polymorphism.md#kinds-and-deferred-expressiveness), not ordinary ADT syntax.

## Null, missing and schema truth need explicit constructors

**[Requirement]** Missing and explicit null remain distinct when required by the schema; forms add empty string and partial editing (Spec S06/S26). **[Proposal]** Model the distinction in a candidate boundary type `Missing | Null | Present(T)`, then let each declared field schema decide accepted cases. Do not reuse one host `nil` for every state before policy. `{}` and `{amount:null}` must take different decoder paths when presence is required. `Present(0)` is different again; treating zero/empty as absence loses data. Tagged ADT discriminants also need unknown-tag/version behavior.

**[Unknown]** BEAML has not chosen numeric overflow, Decimal arithmetic, record equality/order, implicit coercions, union overlap or canonical wire representation. These are reference-informed design choices, not solved by saying “statically typed.”

## Validation probes

**[Proposal]** Pair each typing rule with positive and compile-fail examples; use a tiny reference evaluator for result/error/effect-order differential checks. Include missing ADT arms/guard fallthrough, nominal ID substitution, contravariant callback misuse, writable-record aliasing, absent/null/empty form cases and foreign forged maps. If recovery inserts an error type, code generation must refuse unresolved obligations. Establish exact theorem assumptions before labeling a contract PROVED; tests stay TESTED. [Foundational source map](../../sources/type-system-foundations.md).
