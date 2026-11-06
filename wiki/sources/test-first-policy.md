---
id: source-test-first-policy
kind: source-note
status: adopted-owner-instruction
updated: 2026-11-05
---

# Test-first policy sources

Origin: supplied owner instruction, received through the coordinating agent's task brief on 2026-11-05.
Coverage: selected paraphrases in the [immutable adoption capture](../../raw/requirements/2026-11-05-test-first-policy.md).
The owner requested global adoption and local retention. No full third-party text is retained.

**[Requirement]** Use genuine RED, user review and GREEN for meaningful behavior changes.
Report the test name, expected assertion, actual failure and reason before production implementation.
Wait for review unless the user explicitly waives or preauthorizes the checkpoint.
General task authorization alone does not waive it. Missing imports or broken setup do not establish behavior RED.
The [implementation skill](../../skills/implement-step/SKILL.md#test-first-rule) defines the separate fresh-worker phases.

**[Requirement]** No-behavior prose, docstring, comment, formatting and literal wording changes need no new test.
Strings that affect logic, parsing, protocols or security are behavior changes.
Record concrete reasons when no meaningful automated test is possible. Perform appropriate alternative checks.
Do not mirror implementation text or snapshot trivial wording.
Keep [event-driven main-agent coordination](main-agent-orchestration.md) and secret prohibitions.

**[Verified]** [Official OpenAI Docs](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)
identify global `AGENTS.override.md` precedence over `AGENTS.md` in the Codex home directory.
No global override existed at the requested default installation during this change.
The global `AGENTS.md` and both implementation skill copies now contain the policy.

Limits: instruction files cannot prove future compliance or reload guidance already held by an active run.
A different Codex home or later project instructions can affect discovery or precedence.
This adoption establishes no runtime enforcement, EXPERIMENT result, review round, commit or push.
