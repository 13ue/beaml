# Typed error and replay request

Origin: direct user request in this local conversation, relayed to the authoring agent on 2026-11-05. This is a selective paraphrase, not a verbatim transcript. Local/private; no external publication permission inferred. No personal names or operational payloads retained.

## Requirement R01

The user asks to add Broadway/Kafka knowledge and map event flows to proposed BOUNDED CONTEXTS. The mapping must explain backpressure, replay and failure behavior.

The central target is: when an error occurs, replay the full surrounding execution with types preserved as GROUND TRUTH. The target includes the language/compiler and runtime/Observatory stack. A summary log or a best-effort trace is not a substitute for the requested surrounding context.

This later request expands the historical PDF's fixture/provider-response replay scope. It does not grant permission to collect or read secrets. Existing global prohibitions remain in force. No implementation choice, scheduler interception model, capture policy, retention period or production service is approved by this requirement capture.

## Requirement decomposition for traceability

- R01a: classify event flows and candidate BOUNDED CONTEXT ownership; explain backpressure and failure.
- R01b: preserve TYPED ERROR variants and full relevant ERROR CONTEXT across language/compiler/runtime boundaries.
- R01c: support a fully typed REPLAY RUN of the surrounding execution, rather than rely on log strings.
- R01d: make the original evidence authoritative within its owner and scope; preserve the original when exploring a changed run.
- R01e: expose missing context, uncertain outcomes, divergence and policy restrictions. Do not fabricate completeness.

R01e is an explicit interpretation needed to make the requested target reviewable; exact status vocabulary remains proposed. R01b–d state the user target; the definitions and architecture in the wiki are proposals that operationalize it.
