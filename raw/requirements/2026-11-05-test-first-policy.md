# Global test-first policy: selected adoption capture

Origin: supplied owner conversation, 2026-11-05, relayed through the coordinating agent's task brief.
Coverage: selected paraphrases, not a full transcript. The owner requested global instruction changes and local retention.
Attribution: owner instructions; no complete third-party source or publication rights are included.

## Adopted instruction

**[Requirement]** Use test-first development for meaningful code or behavior changes by default.
Write and run a meaningful test before changing production behavior. Retain genuine RED evidence.
Show the red tests to the user before implementation. Wait for the user's review and instruction to continue.
The owner can explicitly waive or preauthorize this checkpoint. General task authorization alone does not waive it.
After review, implement the smallest complete change and establish GREEN.
Repeat this sequence for each new meaningful behavior step.

**[Requirement]** Report the test name, expected assertion, actual failure and reason.
Missing imports, broken setup and unrelated failures do not establish behavior RED.
Preserve independent tests, review and final verification.
The main agent coordinates fresh workers and presents their evidence. It does not run tools or tests itself.
Keep the existing event-driven coordination and secret prohibitions.

## Sensible exclusions

**[Requirement]** Exclude prose, docstrings, comments, formatting and literal wording changes only when behavior does not change.
Strings that affect logic, parsing, protocols or security remain behavior changes.
When no meaningful automated test is possible, record the concrete reason and perform an appropriate alternative check.
Do not mirror implementation text or snapshot trivial wording.
Explicit owner instructions can change the approach or its scope.

## Scope and limits

The requested global destination is `/Users/lennart/.codex/AGENTS.md`.
Apply the same rule to the repository and installed `implement-step` skills.
Retain task-specific review and waiver instructions in task records, not in the global policy.
This instruction change adds no BEAML runtime behavior and needs no manufactured RED test.
It requires instruction review, skill validation and agreement checks instead.
This capture establishes an adopted instruction, not an EXPERIMENT result or enforcement guarantee.
It does not authorize commits, pushes, publication or changes to concurrent implementation tasks.
