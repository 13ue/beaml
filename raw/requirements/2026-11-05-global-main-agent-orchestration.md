# Global main-agent orchestration adoption: selected capture

Origin: repository-owner conversation, 2026-11-05, supplied through the coordinating agent's task brief.
Coverage: selected paraphrases of the adopted instruction, not a full transcript.
Retention: the owner requested durable global configuration and repository documentation.

**[Requirement]** The user-facing main agent only coordinates workers and responds to the user.
This applies to every task, including reads, research, documentation, configuration, implementation, tests and review.
Fresh workers use GPT-6.1 Sol, Medium effort and no inherited chat history.
Workers perform all substantive work, including ledgers, documentation and final diff inspection.
Workers can use tools and write assigned files. The main-agent restriction does not require recursive delegation.
Keep the main agent responsive. It must not run long tools, builds or tests.
For coding, retain plan, independent Ponytail ultra/lite proposals, solve, test, review, optional single repair and final verification.
The main agent reviews worker reports. It does not read diffs or edit files itself.
Global rules must not contain task-specific authorization.

**[Verified]** Official OpenAI documentation was retrieved on 2026-11-05.
[Custom instructions with AGENTS.md — How Codex discovers guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)
identifies the default Codex home as `~/.codex`.
A non-empty global `AGENTS.override.md` takes precedence over `AGENTS.md`.
Project files closer to the current directory override earlier guidance. Guidance is loaded when a run starts.
No global override file existed when this change was applied.
The existing global `AGENTS.md` was preserved, with the new policy appended.
The repository and installed `implement-step` copies were updated together.

Limits: this is an instruction-file change, not a runtime enforcement mechanism.
It does not prove future agent compliance or change guidance already loaded in a running session.
No secret files or values were read. No EXPERIMENT implementation or result was changed by this configuration work.
The earlier [implementation authorization](2026-11-05-implementation-workflow.md) remains task evidence, outside the global policy.
No review round, commit, push or publication is claimed.
Copyright: owner-supplied requirement paraphrases and researcher notes. No third-party document is copied in full.
