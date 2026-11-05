---
id: source-information-flow-security
title: Information-flow primary sources
kind: source-note
status: verified-upstream-not-beaml
updated: 2026-11-05
---

# Information-flow primary sources

**[Verified]** below means checked in the identified upstream material, not tested or implemented in BEAML. [Selected local evidence capture](../../raw/research/security-observability/2026-11-05-selected-evidence.md) records coverage, attribution, dates and limits. No full papers were imported; no security proof was audited. [BEAML security synthesis](../concepts/information-flow-security.md) separates requirements and proposals.

| Source / version | Evidence inspected | Why relevant / limit |
|---|---|---|
| Cornell [Jif decentralized label model](https://research.cs.cornell.edu/jif/doc/jif-3.3.0/dlm.html), 3.3.0 | Principals/delegation; confidentiality/integrity policies; join/meet operations | Concrete lattice/authority reference; BEAML additionally proposes categories/purpose/recipient dimensions, which are not automatically supplied by copying Jif syntax. |
| Cornell [Jif label checking](https://research.cs.cornell.edu/jif/doc/jif-3.3.0/label_checking.html), 3.3.0 | pc sensitivity; labels for normal and exceptional completion; authority-governed declassification | Branch occurrence and exception behavior can carry secrets. Documentation describes a Java-oriented model, not an OTP formalization. |
| Myers/Liskov, [Protecting Privacy using the Decentralized Label Model](https://www.cs.cornell.edu/andru/papers/iflow-tosem.pdf) | Abstract and bibliographic/selected indexed discussion only | Foundational ownership-based release authority and static checking. Full theorem assumptions not reviewed; ACM copyright retained upstream. |
| Hirsch/Cecchetti, [Giving Semantics to Program-Counter Labels via Secure Effects](https://arxiv.org/abs/2010.13191v2), v2 2020-12-10; POPL 2021 DOI 10.1145/3434316 | Abstract/bibliography | Connects pc to state/exceptions/nontermination effects; warns a simple pc-lower-bound story is not universally valid. This note is a research lead, not a completed formal proof review. |
| EEF Security WG, [Protecting sensitive data](https://security.erlef.org/secure_coding_and_deployment_hardening/sensitive_data.html), accessed 2026-11-05 | Runtime leak surfaces and mitigation sections | BEAM leaks include args, stacktraces, logs, introspection and dumps; Inspect/status/ETS/process controls reduce exposure. They do not turn a wrapper into an isolation boundary or guarantee erasure. |

**[Inference]** Ordinary type validity and confidentiality are different axes. BEAML's `Validated<T>` transition establishes schema conformity; its label/policy system governs where that value may flow. Neither implies factual correctness or authorization by itself. This follows from [Spec p.2 §3 and pp.12-13 §§34-37](engineering-spec-v0.5.md), with the distinctions illustrated by Jif's labeled ordinary types.

**[Unknown]** A BEAML-specific noninterference theorem, termination policy, exception/retry/cancellation semantics, asynchronous pc propagation and trusted computing base have not been supplied. The upstream sources justify studying these questions, not claiming that BEAML inherits their guarantees. The [gap queue](../planning/specification-gaps.md) preserves open decisions.
