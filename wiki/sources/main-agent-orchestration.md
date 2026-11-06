---
id: source-main-agent-orchestration
kind: source-note
status: adopted-owner-instruction
updated: 2026-11-05
---

# Main-agent orchestration sources

Origin: supplied repository-owner instruction, received through the coordinating agent's task brief.
Access date: 2026-11-05. Coverage: selected paraphrases, not a full transcript.
The [immutable capture](../../raw/requirements/2026-11-05-global-main-agent-orchestration.md) records adoption, scope and limits.
The owner authorized local retention and global instruction changes. No full third-party text is retained.

**[Requirement]** The user-facing main agent only coordinates workers and responds to the user, for every task.
Fresh GPT-6.1 Sol Medium workers perform reads, research, records, configuration, implementation, tests and review.
Workers can use tools and write assigned files. This restriction does not require recursive delegation.
The main agent reviews worker reports and stays responsive.
For coding, retain the [implementation pipeline](../../skills/implement-step/SKILL.md).

**[Verified]** [Official OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)
identifies global `AGENTS.override.md` precedence over `AGENTS.md` in the Codex home directory.
Project guidance is applied later. Instruction discovery occurs when a run starts.
The default global installation had no override file when inspected.
The global `AGENTS.md` now includes this rule. The repository and installed skill copies agree after validation.
The [project rule](../../AGENTS.md#main-agent-coordination) applies the same scope within BEAML.

Limits: file validation cannot prove compliance in future chats or reload instructions already held by an active run.
No EXPERIMENT result, runtime enforcement, review round, commit or push is established by this adoption.

**[Requirement]** The [later clarification](../../raw/requirements/2026-11-05-global-main-agent-orchestration-v2.md) requires incoming worker notifications.
The main agent must not poll, sleep, use repeated status reads or block on coordination waits.
It yields to the user when nothing is actionable. Bounded worker subprocess checks remain permitted.
