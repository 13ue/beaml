---
id: concept-information-flow-security
title: BEAML information-flow security design
kind: synthesis
status: research-backed-proposal
updated: 2026-11-05
---

# BEAML information-flow security

**[Requirement]** BEAML proposes preventing unauthorized sensitive flows inside compiler-controlled boundaries. It does not promise secrecy against arbitrary foreign code, compromised hosts or all side channels. Production unclassified sensitive egress fails closed; payload capture stays off. This page interprets the [supplied spec pp.12-14 §§33-46](../sources/engineering-spec-v0.5.md), informed by [primary IFC sources](../sources/information-flow-security.md); no security mechanism is implemented here.

## Labels need a complete algebra

**[Requirement]** Values keep labels through derived values, containers, formatting and errors. A bare String cannot erase a sensitive label. Label dimensions include confidentiality, data category and allowed purpose/recipient; joins combine restrictions. pc tracks secret-dependent branches. Declassification requires a privileged reviewed policy/capability and metadata-only release audit. (Spec p.12 §§34-36.)

**[Proposal]** Before syntax implementation, define a small explicit domain and order. A candidate finite model uses confidentiality `max`, category union, and intersection of allowed recipient/purpose sets when combining data. Empty allowed sets would mean no permitted sink rather than public. This candidate is not a settled BEAML lattice: purpose-dependent authorization, dynamic principals, default universal sets, category constraints and incomparable policies need formal rules before adoption. Cornell's [Jif DLM](https://research.cs.cornell.edu/jif/doc/jif-3.3.0/dlm.html) provides an authority/lattice comparison, not this exact product model.

**[Proposal]** Check finite-model order/join laws (reflexivity, antisymmetry, transitivity; commutative/associative/idempotent least upper bounds), monotonic propagation and sink-policy decisions. Generate negative cases combining innocuous fields into restricted containers. Retain labels in HIR/MIR values, joins/phi nodes, errors and effect obligations, and test each lowering for preservation. These checks operationalize Spec§§43-44; they are not themselves a noninterference proof.

## Control flow is a release channel

```text
if secret_condition { public_sink("yes") }
else                { public_sink("no") }
```

**[Requirement]** This branch leaks even without secret bytes in either literal. v1 rejects analyzable secret-dependent public output; full timing/size/cardinality protections are expressly unclaimed (Spec§35). **[Verified]** [Jif label checking](https://research.cs.cornell.edu/jif/doc/jif-3.3.0/label_checking.html) tracks normal/exception completion as well as pc; the [pc/effects paper abstract](https://arxiv.org/abs/2010.13191v2) motivates treating effects precisely.

**[Proposal]** Start with conservative branch pc joins and explicit rules for errors/early returns, then reject unsupported sensitive control-flow escapes. Add tests for secret-dependent error selection, validation failure detail, exceptions, retries, command cancellation, message send/receive, collection cardinality and public telemetry counters. Do not call all implicit flow “P2”: the [gap queue](../planning/specification-gaps.md) identifies the minimum-v1/advanced-P2 tension. Asynchronous/termination-sensitive guarantees remain **[Unknown]** until formalized.

## Unknown foreign code is an enforcement decision

**[Requirement]** Unknown Elixir calls may leak absent a reviewed effect/taint manifest; macros/NIFs/reflection/dynamic dispatch are UNKNOWN or blocked under strict policy. Ordinary structs are no secrecy barrier. Runtime guards cover the end of static guarantees, while authorized owner/admin rendering is scoped access rather than global public declassification. (Spec p.13 §37; p.14 §§43,45.)

**[Proposal]** An interop manifest should name module/function/arity + artifact/version identity, input/output label relations, effects/sinks, exception behavior, reviewer and evidence scope. A missing/stale manifest stays UNKNOWN; strict sensitive egress refuses it. Treat “analysis unknown,” “runtime allow/deny,” “waiver” and “proof status” as distinct fields. A waiver cannot turn a test into proof. This needs a canonical status enum because the source varies PROVEN/PROVED and ENFORCED/RUNTIME_ENFORCED.

**[Proposal]** Cross-language tests should attempt bypass by direct struct construction, Inspect/String.Chars/JSON encoding, errors with arguments, Ecto/HTTP/LLM logs, PubSub/Oban args, HEEx attributes/flash, process introspection and crash reporting. [EEF runtime guidance](https://security.erlef.org/secure_coding_and_deployment_hardening/sensitive_data.html) identifies mitigation surfaces; they supplement the compiler boundary. Cryptographic isolation/blanket memory zeroization on BEAM remains unclaimed.

## Declassification and release governance

**[Requirement]** Require named policy, reason, principal/purpose, reviewed allowlist, generated callsite ID and metadata audit; masking needs a stated leakage budget/output guarantee. Consent to one render is not permission to export the same value to logs or an LLM. (Spec§§36-37.)

**[Proposal]** First support no general downgrade expression. A deliberately small reviewed release operation can record input/output policy, authorized purpose, version, expiry/revocation and tests, or refuse until policy exists. This is a conservative proposed implementation order, not a source requirement that all release functionality be removed. Declassification authority and untrusted-input validation should stay separate; authenticity/integrity endorsement is another concept, not a synonym for schema validation.

**[Unknown]** The exact TCB, revocation during workflows, principal transport, treatment of mutable foreign state, timing/termination model and proof assumptions need explicit decisions. The first deliverable should be a formal small-core model plus compile-pass/fail corpus and scoped manifest, before a claim that annotations enforce privacy.
