---
id: synthesis-baml-language-and-tooling
title: "BAML language and tooling: what BEAML can borrow"
kind: synthesis
status: proposed
updated: 2026-11-06
---

# BAML language and tooling: what BEAML can borrow

Status: research synthesis and BEAML design hypotheses. No semantics below are adopted merely by appearing here. Retrieved 2026-11-05.

## Evidence tracks

**[Verified]** Upstream facts and **[Proposal]** candidate implications are separated in the table.

[Established documentation](../sources/baml-documentation.md) describes a structured-output DSL with generated SDKs. [Pinned canary compiler](../sources/baml-canary-compiler.md) describes a broader language, typed errors and a new compiler/VM. Mixing those tracks would create a false compatibility target.

**[Verified]** Correction 2026-11-06: the documentation track above is BAML v0. Its pages now call it "the legacy DSL". The canary compiler track is BAML v1, a separate language with its own release line (`baml-language-0.25.1` on 2026-11-06, no 1.0 tag). v1 has a general-purpose standard library (files, processes, HTTP server, crypto), host bridges in many languages and standalone executables. LLM functions are one feature of v1, not the whole language. Do not treat BAML as only an LLM DSL, and do not treat v0 as the current language. [BAML v1 source page](../sources/baml-v1.md)

| Area | BAML evidence | BEAML hypothesis / decision still required |
|---|---|---|
| Familiar surface | Typed function signatures, classes/enums, unions; canary adds general expression/function semantics | Use TypeScript familiarity for discoverability, but publish an independent grammar and soundness contract |
| Prompt functions | Signature + client + Jinja prompt; output schema rendered from types | Keep prompt functions first class; decide whether template evaluation is pure and how holes preserve source spans/security labels |
| Types at runtime | Canary retains concrete nominal types; collections are invariant | Specify BEAM representation, ABI tags, integer range, null/missing, enum and collection semantics before promising interoperability |
| Effects/errors | Canary typed throws has explicit/inferred modes and panic distinction | Align BEAML domain effects/contracts with recoverable errors, cancellation, process exits and foreign exceptions; do not assume they are interchangeable |
| Lowering | AST synthesizes ordinary companion functions and client bindings | Reuse the normalization idea so prompts do not require special cases throughout every compiler layer |
| Incrementality | Salsa query layers, semantic/source-map separation | Share one semantic engine across CLI/LSP/tests, while measuring invalidation with edits rather than assuming it |
| Execution | Canary BexVM engine, async I/O and shared heap; v1 also compiles MIR to Rust and packs standalone executables ([v1](../sources/baml-v1.md#runtime)) | BEAML's generated Elixir/Erlang and OTP runtime need their own scheduler/isolation/lifecycle semantics |
| Tooling | Source fixtures, preview, generated clients, formatter and editor integration | Begin with deterministic syntax/contract diagnostics, prompt preview and fixture evaluation; real LLM tests need explicit provider/version/cost controls |

Sources: [functions](https://docs.boundaryml.com/ref/baml/function), [tests](https://docs.boundaryml.com/ref/baml/test), [pinned architecture/type system](../sources/baml-canary-compiler.md).

**[Verified]** The deeper [source walkthrough](compilers/baml.md) checks actual hir_ty queries, colon/backtick syntax, runtime Schema reflection and shared-T stream defaults. These source-level findings qualify conceptual names and nullable partial-type assumptions in older documentation. [Correction provenance](../../raw/research/baml-internals/record-2026-11-05.md)

## BAML v1 vs BEAM/OTP

**[Inference]** This compares runtime mechanisms only. It is reasoning from code read at pin `989676dd5169497c0d2a8d8e1d10914e987ae262`, not a measurement. It makes no claim that one is better for a given workload. [BAML v1 source page](../sources/baml-v1.md#runtime), [BEAM processes](beam/processes-messages-and-otp.md), [BEAM memory and GC](beam/terms-memory-and-gc.md)

| Topic | BAML v1 (code read, not run) | BEAM/OTP |
|---|---|---|
| Memory and GC | One shared heap for all VMs of an engine. Every collection is full and compacting; running VMs park at safepoints | Private heap per process, per-process GC, copy on send |
| Task isolation | Tasks share the heap and mutable globals. No sandbox or capability model found | Processes share no mutable heap data. Shared ETS and binaries are separate cases |
| Failure handling | Cancellation cascades down the spawn tree. Unobserved errors are reported. No supervision, links or monitors found | Links, monitors and supervisors with restart strategies |
| Durability | None on the default branch. Draft pull request #4956 (heap snapshots) is open since 2026-09-21 | None built in for process state. Durability needs an explicit store, event log or CHECKPOINT |
| Retries and timeouts | Library code: `ai.clients.Retry` with a retry safety gate; `with_timeout` built on `spawn`, `CancelToken` and `sleep` | Library and application code: receive timeouts, `Task` timeouts, supervisor restart limits |

**[Inference]** Process isolation, per-process GC and supervision come from the BEAM VM and OTP, not from BEAML language rules. A BEAML design gets them only if its generated code uses processes and supervision correctly.

**[Inference]** OTP restarts do not settle uncertain external effects ([round 3, objection 3](../planning/roasting-rounds.md#3-otp-restarts-processes-it-cannot-settle-an-uncertain-payment)). Restart semantics alone do not give BEAML an advantage in correctness for model calls.

**[Unknown]** Upstream plans for supervision, distribution or hot code loading; the outcome of #4956; relative performance. No benchmark was run.

## Smallest useful compatibility boundary

**[Proposal]** This is a suggested scope, not an accepted compatibility promise.

A design proposal is to support the concepts first, with an explicit future import subset. Name that subset rather than claiming general BAML compatibility. Test corpus categories would include scalar/enum/class/list/union schemas, Jinja rendering and message boundaries, type-to-prompt format, repaired output, ambiguous unions, validation errors, and partial-to-final transitions. No import tool or compatibility layer is implemented.

For a TypeScript-like surface, decide separately whether class fields use `name: Type` or the established BAML `name Type`, whether return arrows remain, which statements and expressions exist, and whether union order is semantic only at parsing boundaries. Familiar punctuation cannot resolve these semantic choices. [Type reference](https://docs.boundaryml.com/ref/baml/types), [canary subtyping](../sources/baml-canary-compiler.md)

## Security and runtime gaps

**[Inference]** These implications follow from the documented runtime choices and BEAML specification.

Provider selection, runtime client overrides and fallback can change the recipient of prompt data. BEAML policy must authorize each resolved destination, including subsequent attempts; a declared client name alone is insufficient evidence. Template control flow and schema descriptions can expose data even when interpolated values are labeled. This is BEAML analysis, not a claim that BAML implements information-flow labels. [Client registry](https://docs.boundaryml.com/guide/baml-advanced/llm-client-registry), [fallback](https://docs.boundaryml.com/ref/llm-client-strategies/fallback)

An unstable community Elixir integration is not an alternative proof of the proposed BEAM compiler/ABI. Establish a small generated-module call with validated input/output, structured errors, cancellation and source-location mapping before scaling the runtime. [Elixir status](https://docs.boundaryml.com/guide/installation-language/elixir)

See [structured output and streaming](structured-output-and-streaming.md) and [reuse constraints](../sources/baml-license.md).
