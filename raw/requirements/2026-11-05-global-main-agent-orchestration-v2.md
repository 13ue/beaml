# Global main-agent orchestration: event-driven clarification

Origin: repository-owner conversation, 2026-11-05, supplied through the coordinating agent's task brief.
Coverage: selected paraphrases, not a full transcript. Retention follows the owner's global configuration request.
This capture follows the [first adoption capture](2026-11-05-global-main-agent-orchestration.md), which remains unchanged.

**[Requirement]** The owner rejects repeated short coordination waits as well as long blocking waits.
The user-facing main agent uses incoming worker notifications and does not poll.
Workers send milestone, blocker and completion notifications.
The main agent dispatches work, handles incoming events and yields to the user when nothing is actionable.
It does not use `wait_agent` loops, sleep, repeated agent/status reads or blocking tool waits.
Worker subprocess lifecycle checks remain permitted when bounded and required for assigned work.
This clarification changes the global policy and both implementation skill copies.

Limits: instruction files cannot prove future compliance or reload guidance held by an active run.
This record reports an adopted instruction, not an EXPERIMENT result or a new review round.
No secrets, complete third-party text or publication rights are included.
