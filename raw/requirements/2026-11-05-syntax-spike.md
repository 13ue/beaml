# Selected syntax and R&D requirements

Origin: owner-supplied conversation in the BEAML project on 2026-11-05.
Coverage: selected paraphrases of the accepted syntax and experiment request, not a full conversation export.
Publisher: repository owner. Status: requested experimental behavior, not a complete language specification.
Rights: original project requirement notes; no third-party text copied.

- Define exact data interfaces with required typed fields. Reject missing and additional fields during construction.
- Match nested variant and record values in top-level function clauses.
- Omit the outer parameter parentheses in function definitions. Separate multiple parameters with commas.
- Use parentheses on function calls and variant constructors, without a space before the opening parenthesis.
- Use commas between call and constructor arguments.
- Select record fields in patterns without a remainder marker. Unselected fields still belong to the exact input contract.
- Start a small proof of concept that translates this subset into code executed on the BEAM.
- Change this repository into an R&D repository. Record experiments in an R&D process with domain ownership and results.

Limits: generic syntax, higher-kinded types, methods/capabilities, effects, polymorphic inference and production release rules remain unsettled.
