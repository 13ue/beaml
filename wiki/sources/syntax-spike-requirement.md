---
id: source-syntax-spike-requirement
kind: source-note
status: owner-requirement
updated: 2026-11-05
---

# Syntax spike requirement

**[Requirement]** Origin: owner-supplied conversation on 2026-11-05. Publisher: repository owner. No upstream URL or version applies.
The [selected requirement capture](../../raw/requirements/2026-11-05-syntax-spike.md) records accepted syntax and the R&D request.
Coverage is selected paraphrases, not a full transcript or complete grammar. No third-party text is copied.

Definitions omit outer parameter parentheses. Calls and variant constructors use parentheses and comma-separated arguments.
Exact data interfaces require all declared fields at construction and reject extra fields. Record patterns select fields without `..`.
Nested top-level clauses are required. The first proof of concept must generate code that executes on the BEAM.
The repository must retain experiments, their context ownership, acceptance criteria and evidence.

**[Requirement]** The owner later adopted generated Elixir as the initial backend. The Elixir/OTP compiler produces BEAM modules.
The [separate decision capture](../../raw/requirements/2026-11-05-elixir-backend-decision.md) preserves this change without replacing the earlier capture.
Direct BEAM assembly or bytecode emission is not an adopted later goal. Future backend changes remain open decisions.

**[Proposal]** [EXPERIMENT 0001](../../experiments/0001-syntax-to-beam/README.md) uses Rust for the compiler probe.
It limits TYPE support to String, finite acyclic interfaces and concrete enums. Generics are deferred, not rejected for the language.
Interfaces with methods, broader inference, block syntax and production assurance remain unknown.

See the [R&D register](../planning/research-and-development.md), [context map](../planning/context-map.md) and [historical specification](engineering-spec-v0.5.md).
This request adopts a small experimental syntax. It does not complete the historical M0 or M3 gates.
