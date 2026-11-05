---
id: synthesis-baml-language-and-tooling
title: "BAML language and tooling: what BEAML can borrow"
kind: synthesis
status: proposed
updated: 2026-11-05
---

# BAML language and tooling: what BEAML can borrow

Status: research synthesis and BEAML design hypotheses. No semantics below are adopted merely by appearing here. Retrieved 2026-11-05.

## Evidence tracks

**[Verified]** Upstream facts and **[Proposal]** candidate implications are separated in the table.

[Established documentation](../sources/baml-documentation.md) describes a structured-output DSL with generated SDKs. [Pinned canary compiler](../sources/baml-canary-compiler.md) describes a broader language, typed errors and a new compiler/VM. Mixing those tracks would create a false compatibility target.

| Area | BAML evidence | BEAML hypothesis / decision still required |
|---|---|---|
| Familiar surface | Typed function signatures, classes/enums, unions; canary adds general expression/function semantics | Use TypeScript familiarity for discoverability, but publish an independent grammar and soundness contract |
| Prompt functions | Signature + client + Jinja prompt; output schema rendered from types | Keep prompt functions first class; decide whether template evaluation is pure and how holes preserve source spans/security labels |
| Types at runtime | Canary retains concrete nominal types; collections are invariant | Specify BEAM representation, ABI tags, integer range, null/missing, enum and collection semantics before promising interoperability |
| Effects/errors | Canary typed throws has explicit/inferred modes and panic distinction | Align BEAML domain effects/contracts with recoverable errors, cancellation, process exits and foreign exceptions; do not assume they are interchangeable |
| Lowering | AST synthesizes ordinary companion functions and client bindings | Reuse the normalization idea so prompts do not require special cases throughout every compiler layer |
| Incrementality | Salsa query layers, semantic/source-map separation | Share one semantic engine across CLI/LSP/tests, while measuring invalidation with edits rather than assuming it |
| Execution | Canary BexVM engine, async I/O and shared heap | BEAML's generated Elixir/Erlang and OTP runtime need their own scheduler/isolation/lifecycle semantics |
| Tooling | Source fixtures, preview, generated clients, formatter and editor integration | Begin with deterministic syntax/contract diagnostics, prompt preview and fixture evaluation; real LLM tests need explicit provider/version/cost controls |

Sources: [functions](https://docs.boundaryml.com/ref/baml/function), [tests](https://docs.boundaryml.com/ref/baml/test), [pinned architecture/type system](../sources/baml-canary-compiler.md).

## Smallest useful compatibility boundary

**[Proposal]** This is a suggested scope, not an accepted compatibility promise.

A design proposal is to support the concepts first, with an explicit future import subset. Name that subset rather than claiming general BAML compatibility. Test corpus categories would include scalar/enum/class/list/union schemas, Jinja rendering and message boundaries, type-to-prompt format, repaired output, ambiguous unions, validation errors, and partial-to-final transitions. No import tool or compatibility layer is implemented.

For a TypeScript-like surface, decide separately whether class fields use `name: Type` or the established BAML `name Type`, whether return arrows remain, which statements and expressions exist, and whether union order is semantic only at parsing boundaries. Familiar punctuation cannot resolve these semantic choices. [Type reference](https://docs.boundaryml.com/ref/baml/types), [canary subtyping](../sources/baml-canary-compiler.md)

## Security and runtime gaps

**[Inference]** These implications follow from the documented runtime choices and BEAML specification.

Provider selection, runtime client overrides and fallback can change the recipient of prompt data. BEAML policy must authorize each resolved destination, including subsequent attempts; a declared client name alone is insufficient evidence. Template control flow and schema descriptions can expose data even when interpolated values are labeled. This is BEAML analysis, not a claim that BAML implements information-flow labels. [Client registry](https://docs.boundaryml.com/guide/baml-advanced/llm-client-registry), [fallback](https://docs.boundaryml.com/ref/llm-client-strategies/fallback)

An unstable community Elixir integration is not an alternative proof of the proposed BEAM compiler/ABI. Establish a small generated-module call with validated input/output, structured errors, cancellation and source-location mapping before scaling the runtime. [Elixir status](https://docs.boundaryml.com/guide/installation-language/elixir)

See [structured output and streaming](structured-output-and-streaming.md) and [reuse constraints](../sources/baml-license.md).
