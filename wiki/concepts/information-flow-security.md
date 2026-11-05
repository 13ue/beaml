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

## Worked policy algebra and its design boundaries

**[Proposal]** This finite candidate makes “join restrictions” testable. It is explanatory mathematics, not accepted BEAML syntax/policy. Let a label be `(c,K,R,P)`: c is an ordered confidentiality level; K a set of data categories; R allowed recipients; P allowed purposes. Fix finite universes of categories/recipients/purposes for the model. Define `L1 <= L2` when `c1<=c2`, `K1⊆K2`, `R2⊆R1`, and `P2⊆P1`; moving upward adds restrictions. A join is `(max(c1,c2), K1∪K2, R1∩R2, P1∩P2)`. Bottom has public confidentiality, no categories and unrestricted recipient/purpose universes. Top permits no recipient/purpose. An empty R/P is deny, not “unknown means everyone.”

Take email `(confidential,{pii},{billing_ui,mailer},{invoice_support})` and token `(secret,{credential},{provider_A},{inference})`. A formatted combination has secret level, both categories, and empty recipient/purpose intersections. It cannot go to either mailer or provider_A without a distinct explicit reviewed release. Relabeling it Public because the output is a String would violate the order. A browser authorization granting owner access can narrow an allowed recipient context; it does not create global Public data.

**[Verified]** [Jif's labeled-type flow order and authority reference](https://research.cs.cornell.edu/jif/doc/jif-3.3.0/language.html#labeled-types) supplies an example of preserving restrictions through joins and requiring authority for downgrading. **[Inference]** BEAML's category/purpose model needs its own proof: a simple product may be too weak for correlated rules such as “recipient A for purpose X OR recipient B for purpose Y.” Independent R/P sets can accidentally allow unintended cross-products. A policy-as-predicate or disjunction-of-authorized-pairs model could retain correlations; that is an unresolved design choice, not missing knowledge that can be resolved by adopting a tuple silently.

**[Proposal]** Define `can_flow` as a checked relation between a label, sink capabilities and authenticated context, not label ordering alone. For candidate context `(principal,tenant,purpose,recipient,policy_version)`, require clearance for c/categories, membership in permitted recipient/purpose policy, tenant/resource authorization and valid version/revocation status. Never derive authenticated principal from user JSON or OTel baggage. Test join/order laws plus contextual denies, empty sets, correlated-pair cases and stale principal state. If dynamic context is unavailable, classify the result UNKNOWN and let production enforcement fail closed.

## A pc and exception walk-through

**[Proposal]** In a two-point Public<=Secret model, start `pc=Public`. Reading secret data creates a Secret value. Branching on it joins Secret into the branch pc. Writing a public sink in either branch checks `join(pc,label(value))<=Public`; even public literal text fails. A CFG merge cannot simply discard the branch's information when assigned results, exceptional exits or whether control reaches the merge depend on the secret.

```text
try {
  if secret_flag { raise BadInput }
} catch BadInput {
  public_log("bad")
}
public_log("finished")
```

**[Proposal]** `bad` discloses secret_flag by event presence. If catch normalizes the error but one path terminates/cancels before `finished`, event occurrence can still reveal control information. Conservatively propagate exception/normal-completion labels to the catch/continuation rules or reject unsupported cases. Do not assume redacting exception text removes the leak. An error counter increment can have the same disclosure. Jif's normal/exception label model is reference evidence in the [source note](../sources/information-flow-security.md); BEAML must define its own Result/exception/process-exit/cancel observation model.

Termination-insensitive noninterference compares suitably observable outcomes when runs complete; termination-sensitive claims additionally consider completion itself. Timing/scheduler/network channels make a stronger BEAM theorem materially different. **[Proposal]** State exactly which observations and foreign assumptions the first theorem includes, e.g. a sequential supported core with explicit effect traces and authorized releases. A set of compile-fail examples checks regressions against that model; it does not establish all concurrent-host behavior.

## Make the trusted computing base concrete

**[Requirement]** Spec§33 requires a declared TCB and scoped assurances. **[Proposal]** List the minimum trusted pieces by the failures that would defeat the guarantee:

| Trusted component | Failure that bypasses the intended boundary | First evidence |
|---|---|---|
| Parser/resolver/type+label inference | Wrong binding or erased label gives false Public | Shadowing/alias/container/Unicode source fixtures |
| MIR transformations and sink verifier | Rewrite drops pc/security effects or moves a sink | Pass invariants +metamorphic/differential sink traces |
| Codegen/runtime guards/interop manifest | Generated API/foreign implementation accepts forged evidence or lies about egress | Adversarial ABI +manifest-version/callsite tests |
| Policy/identity/secret configuration | Wrong tenant/principal, stale revoked authority, permissive unknown | Auth-context/revocation tests and reviewed policy version |
| Local telemetry adapter/exporter/loggers | Auto-inspect or exception path emits a rejected value before filtering | Canary injection through every configured sink |
| OTP/native libraries/OS/operators/storage | Reflection, dumps, NIF, host access or backups reveal memory/data | Operational hardening/runbooks; explicit non-guarantees |

Keep reviewed code/library identities in the manifest, not just unqualified function names. A dependency update invalidates assumptions until its effect/label contract is checked. The TCB can be reduced or differently partitioned later; it cannot be removed by calling a function “safe.”

## Release authority, dynamic checks and UNKNOWN evidence

**[Proposal]** A release entry should identify input policy, output guarantee, subject/resource scope, purpose/recipient, principal authority, reviewer/policy version, expiry/revocation, operation implementation hash, callsite/source artifact and metadata audit class. For masked email, the guarantee might permit a specified suffix/domain reveal rather than declare anonymity. A salted hash/pseudonym still needs a linkability/leakage model. Tests include repeated releases/composition: two individually allowed masked variants can jointly reveal more than either alone.

**[Verified]** [Jif authority/downgrading](https://research.cs.cornell.edu/jif/doc/jif-3.3.0/language.html#downgrading) distinguishes confidentiality release from endorsement of integrity and constrains runtime security checks themselves. **[Proposal]** In BEAML, a failed `can_view(customer)` message must not reveal a hidden customer exists. Normalize unauthorized errors under a declared policy, and label even allow/deny observations if their computation used sensitive facts. An explicit annotation does not grant authority.

A machine-readable result can contain separate fields: `obligation_kind`, `analysis_status`, `enforcement_action`, `assumptions`, `evidence_ref`, `source/build/policy_version`, `unknown_reason`, `waiver_ref`. A dynamic call might be UNKNOWN statically and BLOCKED at runtime; another supported check may be RUNTIME_ENFORCED. Store both rather than overwriting UNKNOWN with “safe.” Canary tests verify configured sinks only, with no proof claim. **[Unknown]** The canonical enum, formal model, policy language and secure async context transport remain BEAML decisions; the [coverage matrix](../planning/build-readiness.md) should distinguish this design work from reference research and executed validation.
